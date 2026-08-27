import pytest

from conftest import create_plant, register_tenant_headers


@pytest.fixture()
def setup(client):
    headers = register_tenant_headers(client)
    plant_id = create_plant(client, headers)
    item_id = client.post(
        "/api/inventory/items",
        json={"sku": "FG-BRACKET", "name": "Steel Bracket", "item_type": "finished_good", "uom": "EA"},
        headers=headers,
    ).json()["id"]
    asset_id = client.post(
        "/api/maintenance/assets", json={"plant_id": plant_id, "name": "CNC Mill #1", "code": "CNC-1"}, headers=headers
    ).json()["id"]

    return {"headers": headers, "plant_id": plant_id, "item_id": item_id, "asset_id": asset_id}


def test_work_order_lifecycle_updates_asset_status(client, setup):
    headers = setup["headers"]
    wo = client.post(
        "/api/maintenance/work-orders",
        json={"plant_id": setup["plant_id"], "asset_id": setup["asset_id"], "work_order_type": "corrective"},
        headers=headers,
    ).json()
    assert wo["status"] == "open"

    started = client.post(f"/api/maintenance/work-orders/{wo['id']}/start", headers=headers)
    assert started.status_code == 200
    assert started.json()["status"] == "in_progress"

    asset_after_start = client.get("/api/maintenance/assets", headers=headers).json()[0]
    assert asset_after_start["status"] == "maintenance"

    completed = client.post(f"/api/maintenance/work-orders/{wo['id']}/complete", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    asset_after_complete = client.get("/api/maintenance/assets", headers=headers).json()[0]
    assert asset_after_complete["status"] == "operational"


def test_completing_open_work_order_rejected(client, setup):
    headers = setup["headers"]
    wo = client.post(
        "/api/maintenance/work-orders",
        json={"plant_id": setup["plant_id"], "asset_id": setup["asset_id"], "work_order_type": "preventive"},
        headers=headers,
    ).json()

    response = client.post(f"/api/maintenance/work-orders/{wo['id']}/complete", headers=headers)
    assert response.status_code == 409


def test_cancel_in_progress_work_order_restores_asset(client, setup):
    headers = setup["headers"]
    wo = client.post(
        "/api/maintenance/work-orders",
        json={"plant_id": setup["plant_id"], "asset_id": setup["asset_id"], "work_order_type": "corrective"},
        headers=headers,
    ).json()
    client.post(f"/api/maintenance/work-orders/{wo['id']}/start", headers=headers)

    cancelled = client.post(f"/api/maintenance/work-orders/{wo['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    asset = client.get("/api/maintenance/assets", headers=headers).json()[0]
    assert asset["status"] == "operational"


def test_inspection_without_defects_passes(client, setup):
    headers = setup["headers"]
    response = client.post(
        "/api/quality/inspections",
        json={"plant_id": setup["plant_id"], "item_id": setup["item_id"], "inspected_quantity": "50"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["result"] == "pass"
    assert response.json()["defects"] == []


def test_inspection_with_defects_fails_and_defects_resolvable(client, setup):
    headers = setup["headers"]
    response = client.post(
        "/api/quality/inspections",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "inspected_quantity": "50",
            "defects": [{"defect_type": "surface scratch", "severity": "minor", "quantity": "3"}],
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["result"] == "fail"
    defect_id = body["defects"][0]["id"]
    assert body["defects"][0]["status"] == "open"

    resolved = client.post(f"/api/quality/defects/{defect_id}/resolve", headers=headers)
    assert resolved.status_code == 200
    assert resolved.json()["defects"][0]["status"] == "resolved"

    again = client.post(f"/api/quality/defects/{defect_id}/resolve", headers=headers)
    assert again.status_code == 409
