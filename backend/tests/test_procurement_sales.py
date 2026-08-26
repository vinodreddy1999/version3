import pytest

from conftest import register_tenant_headers


@pytest.fixture()
def setup(client):
    headers = register_tenant_headers(client)

    company_id = client.post(
        "/api/org/companies", json={"name": "Acme East", "code": "ACME-E"}, headers=headers
    ).json()["id"]
    plant_id = client.post(
        "/api/org/plants", json={"company_id": company_id, "name": "Plant 1", "code": "P1"}, headers=headers
    ).json()["id"]
    item_id = client.post(
        "/api/inventory/items",
        json={"sku": "RM-001", "name": "Steel Coil", "item_type": "raw_material", "uom": "KG"},
        headers=headers,
    ).json()["id"]

    supplier_id = client.post(
        "/api/procurement/suppliers", json={"name": "SteelCo", "code": "SUP-1"}, headers=headers
    ).json()["id"]
    customer_id = client.post(
        "/api/sales/customers", json={"name": "Bracket Buyers", "code": "CUST-1"}, headers=headers
    ).json()["id"]

    return {
        "headers": headers,
        "plant_id": plant_id,
        "item_id": item_id,
        "supplier_id": supplier_id,
        "customer_id": customer_id,
    }


def test_purchase_order_receive_increases_stock(client, setup):
    headers = setup["headers"]
    po = client.post(
        "/api/procurement/orders",
        json={
            "plant_id": setup["plant_id"],
            "supplier_id": setup["supplier_id"],
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "100", "unit_price": "5"}],
        },
        headers=headers,
    ).json()
    assert po["status"] == "draft"

    client.post(f"/api/procurement/orders/{po['id']}/submit", headers=headers)
    line_id = po["lines"][0]["id"]

    partial = client.post(
        f"/api/procurement/orders/{po['id']}/receive", json={"line_id": line_id, "quantity": "60"}, headers=headers
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "partially_received"

    final = client.post(
        f"/api/procurement/orders/{po['id']}/receive", json={"line_id": line_id, "quantity": "40"}, headers=headers
    )
    assert final.json()["status"] == "received"

    balances = client.get("/api/inventory/balances", headers=headers).json()
    assert balances[0]["quantity_on_hand"] == "100.0000"


def test_receive_beyond_ordered_rejected(client, setup):
    headers = setup["headers"]
    po = client.post(
        "/api/procurement/orders",
        json={
            "plant_id": setup["plant_id"],
            "supplier_id": setup["supplier_id"],
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "10"}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/procurement/orders/{po['id']}/submit", headers=headers)

    response = client.post(
        f"/api/procurement/orders/{po['id']}/receive",
        json={"line_id": po["lines"][0]["id"], "quantity": "11"},
        headers=headers,
    )
    assert response.status_code == 422


def test_receive_before_submit_rejected(client, setup):
    headers = setup["headers"]
    po = client.post(
        "/api/procurement/orders",
        json={
            "plant_id": setup["plant_id"],
            "supplier_id": setup["supplier_id"],
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "10"}],
        },
        headers=headers,
    ).json()

    response = client.post(
        f"/api/procurement/orders/{po['id']}/receive",
        json={"line_id": po["lines"][0]["id"], "quantity": "5"},
        headers=headers,
    )
    assert response.status_code == 409


def test_sales_order_ship_decreases_stock(client, setup):
    headers = setup["headers"]
    client.post(
        "/api/inventory/movements",
        json={"plant_id": setup["plant_id"], "item_id": setup["item_id"], "movement_type": "receipt", "quantity": "50"},
        headers=headers,
    )

    so = client.post(
        "/api/sales/orders",
        json={
            "plant_id": setup["plant_id"],
            "customer_id": setup["customer_id"],
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "30", "unit_price": "12"}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/sales/orders/{so['id']}/confirm", headers=headers)

    response = client.post(
        f"/api/sales/orders/{so['id']}/ship", json={"line_id": so["lines"][0]["id"], "quantity": "30"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "shipped"

    balances = client.get("/api/inventory/balances", headers=headers).json()
    assert balances[0]["quantity_on_hand"] == "20.0000"


def test_ship_beyond_available_stock_rejected(client, setup):
    headers = setup["headers"]
    client.post(
        "/api/inventory/movements",
        json={"plant_id": setup["plant_id"], "item_id": setup["item_id"], "movement_type": "receipt", "quantity": "5"},
        headers=headers,
    )
    so = client.post(
        "/api/sales/orders",
        json={
            "plant_id": setup["plant_id"],
            "customer_id": setup["customer_id"],
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "30"}],
        },
        headers=headers,
    ).json()
    client.post(f"/api/sales/orders/{so['id']}/confirm", headers=headers)

    response = client.post(
        f"/api/sales/orders/{so['id']}/ship", json={"line_id": so["lines"][0]["id"], "quantity": "30"}, headers=headers
    )
    assert response.status_code == 422
