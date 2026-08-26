import pytest

from conftest import other_tenant_headers, register_tenant_headers


@pytest.fixture()
def busy_tenant(client):
    headers = register_tenant_headers(client)

    company_id = client.post(
        "/api/org/companies", json={"name": "Acme East", "code": "ACME-E"}, headers=headers
    ).json()["id"]
    plant_id = client.post(
        "/api/org/plants", json={"company_id": company_id, "name": "Plant 1", "code": "P1"}, headers=headers
    ).json()["id"]

    steel_id = client.post(
        "/api/inventory/items",
        json={
            "sku": "RM-STEEL",
            "name": "Steel Sheet",
            "item_type": "raw_material",
            "uom": "KG",
            "reorder_point": "20",
        },
        headers=headers,
    ).json()["id"]
    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": steel_id, "movement_type": "receipt", "quantity": "10"},
        headers=headers,
    )

    supplier_id = client.post(
        "/api/procurement/suppliers", json={"name": "SteelCo", "code": "SUP-1"}, headers=headers
    ).json()["id"]
    po = client.post(
        "/api/procurement/orders",
        json={
            "plant_id": plant_id,
            "supplier_id": supplier_id,
            "lines": [{"item_id": steel_id, "quantity_ordered": "100"}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/procurement/orders/{po['id']}/submit", headers=headers)
    client.post(
        f"/api/procurement/orders/{po['id']}/receive",
        json={"line_id": po["lines"][0]["id"], "quantity": "30"},
        headers=headers,
    )

    asset_id = client.post(
        "/api/maintenance/assets", json={"plant_id": plant_id, "name": "CNC Mill", "code": "CNC-1"}, headers=headers
    ).json()["id"]
    wo = client.post(
        "/api/maintenance/work-orders",
        json={"plant_id": plant_id, "asset_id": asset_id, "work_order_type": "corrective"},
        headers=headers,
    ).json()
    client.post(f"/api/maintenance/work-orders/{wo['id']}/start", headers=headers)

    client.post(
        "/api/quality/inspections",
        json={
            "plant_id": plant_id,
            "item_id": steel_id,
            "inspected_quantity": "10",
            "defects": [{"defect_type": "dent", "severity": "minor", "quantity": "1"}],
        },
        headers=headers,
    )

    return {"headers": headers, "plant_id": plant_id, "steel_id": steel_id}


def test_dashboard_reflects_real_data(client, busy_tenant):
    headers = busy_tenant["headers"]
    response = client.get("/api/reports/dashboard", headers=headers)
    assert response.status_code == 200
    body = response.json()

    # 10 received + 30 received from PO = 40 on hand, below reorder point 20? no, 40 >= 20.
    assert body["inventory"]["active_item_count"] == 1
    assert body["inventory"]["total_quantity_on_hand"] == "40.0000"
    assert body["inventory"]["low_stock_item_count"] == 0

    assert body["procurement"]["open_purchase_orders"] == 1
    assert body["procurement"]["outstanding_quantity_ordered"] == "70.0000"

    assert body["maintenance"]["open_work_orders"] == 1
    assert body["maintenance"]["assets_down_or_in_maintenance"] == 1

    assert body["quality"]["total_inspections"] == 1
    assert body["quality"]["failed_inspections"] == 1
    assert body["quality"]["open_defects"] == 1


def test_dashboard_isolated_per_tenant(client, busy_tenant):
    other_headers = other_tenant_headers(client)

    response = client.get("/api/reports/dashboard", headers=other_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["inventory"]["active_item_count"] == 0
    assert body["procurement"]["open_purchase_orders"] == 0
    assert body["quality"]["total_inspections"] == 0


def test_dashboard_requires_authentication(client):
    response = client.get("/api/reports/dashboard")
    assert response.status_code == 401
