import pytest

from conftest import create_item, create_plant, register_tenant_headers


@pytest.fixture()
def setup(client):
    headers = register_tenant_headers(client)
    plant_id = create_plant(client, headers)
    item_id = create_item(client, headers)
    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "receipt", "quantity": "100"},
        headers=headers,
    )

    warehouse_id = client.post(
        "/api/warehouse/warehouses", json={"plant_id": plant_id, "name": "Main WH", "code": "WH1"}, headers=headers
    ).json()["id"]
    zone_id = client.post(
        "/api/warehouse/zones",
        json={"warehouse_id": warehouse_id, "name": "Storage", "code": "Z1", "zone_type": "storage"},
        headers=headers,
    ).json()["id"]
    bin_id = client.post("/api/warehouse/bins", json={"zone_id": zone_id, "code": "B1"}, headers=headers).json()["id"]

    return {
        "headers": headers,
        "plant_id": plant_id,
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "zone_id": zone_id,
        "bin_id": bin_id,
    }


def test_putaway_task_completion_increases_bin_stock(client, setup):
    headers = setup["headers"]
    task = client.post(
        "/api/warehouse/putaway-tasks",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "destination_bin_id": setup["bin_id"],
            "quantity": "50",
        },
        headers=headers,
    ).json()

    response = client.post(f"/api/warehouse/putaway-tasks/{task['id']}/complete", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    bin_stock = client.get("/api/warehouse/bin-stock", headers=headers).json()
    assert bin_stock[0]["quantity"] == "50.0000"


def test_completing_task_twice_fails(client, setup):
    headers = setup["headers"]
    task = client.post(
        "/api/warehouse/putaway-tasks",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "destination_bin_id": setup["bin_id"],
            "quantity": "50",
        },
        headers=headers,
    ).json()
    client.post(f"/api/warehouse/putaway-tasks/{task['id']}/complete", headers=headers)
    response = client.post(f"/api/warehouse/putaway-tasks/{task['id']}/complete", headers=headers)
    assert response.status_code == 409


def test_pick_task_completion_decreases_bin_and_plant_stock(client, setup):
    headers = setup["headers"]
    putaway = client.post(
        "/api/warehouse/putaway-tasks",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "destination_bin_id": setup["bin_id"],
            "quantity": "50",
        },
        headers=headers,
    ).json()
    client.post(f"/api/warehouse/putaway-tasks/{putaway['id']}/complete", headers=headers)

    pick = client.post(
        "/api/warehouse/pick-tasks",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "source_bin_id": setup["bin_id"],
            "quantity": "20",
        },
        headers=headers,
    ).json()
    response = client.post(f"/api/warehouse/pick-tasks/{pick['id']}/complete", headers=headers)
    assert response.status_code == 200

    bin_stock = client.get("/api/warehouse/bin-stock", headers=headers).json()
    assert bin_stock[0]["quantity"] == "30.0000"

    balances = client.get("/api/inventory/balances", headers=headers).json()
    assert balances[0]["quantity_on_hand"] == "80.0000"


def test_pick_task_over_bin_stock_rejected(client, setup):
    headers = setup["headers"]
    pick = client.post(
        "/api/warehouse/pick-tasks",
        json={
            "plant_id": setup["plant_id"],
            "item_id": setup["item_id"],
            "source_bin_id": setup["bin_id"],
            "quantity": "10",
        },
        headers=headers,
    ).json()
    response = client.post(f"/api/warehouse/pick-tasks/{pick['id']}/complete", headers=headers)
    assert response.status_code == 422
