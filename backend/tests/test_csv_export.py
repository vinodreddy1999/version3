import csv
import io

import pytest

from conftest import create_customer, create_item, create_plant, create_supplier, register_tenant_headers


@pytest.fixture()
def setup(client):
    headers = register_tenant_headers(client)
    plant_id = create_plant(client, headers)
    item_id = create_item(client, headers)
    supplier_id = create_supplier(client, headers)
    customer_id = create_customer(client, headers)

    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "receipt", "quantity": "50"},
        headers=headers,
    )

    return {
        "headers": headers,
        "plant_id": plant_id,
        "item_id": item_id,
        "supplier_id": supplier_id,
        "customer_id": customer_id,
    }


def _rows(response):
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    return list(csv.reader(io.StringIO(response.text)))


def test_export_items(client, setup):
    response = client.get("/api/inventory/items/export", headers=setup["headers"])
    rows = _rows(response)
    assert rows[0] == ["SKU", "Name", "Type", "UoM", "Reorder Point", "Active"]
    assert rows[1][0] == "RM-001"


def test_export_balances(client, setup):
    response = client.get("/api/inventory/balances/export", headers=setup["headers"])
    rows = _rows(response)
    assert rows[0] == ["SKU", "Name", "On Hand", "Reserved", "Available"]
    assert rows[1] == ["RM-001", "Steel Coil", "50.0000", "0.0000", "50.0000"]


def test_export_movements(client, setup):
    response = client.get("/api/inventory/movements/export", headers=setup["headers"])
    rows = _rows(response)
    assert rows[0] == ["Date", "SKU", "Type", "Quantity", "Reference", "Notes"]
    assert rows[1][1] == "RM-001"
    assert rows[1][2] == "receipt"


def test_export_purchase_orders(client, setup):
    headers = setup["headers"]
    client.post(
        "/api/procurement/orders",
        json={
            "plant_id": setup["plant_id"],
            "supplier_id": setup["supplier_id"],
            "reference": "PO-EXPORT-1",
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "10", "unit_price": "3"}],
        },
        headers=headers,
    )

    response = client.get("/api/procurement/orders/export", headers=headers)
    rows = _rows(response)
    assert rows[0] == ["Reference", "Supplier", "Status", "SKU", "Ordered", "Received", "Unit Price"]
    assert rows[1] == ["PO-EXPORT-1", "SteelCo", "draft", "RM-001", "10.0000", "0.0000", "3.0000"]


def test_export_sales_orders(client, setup):
    headers = setup["headers"]
    client.post(
        "/api/sales/orders",
        json={
            "plant_id": setup["plant_id"],
            "customer_id": setup["customer_id"],
            "reference": "SO-EXPORT-1",
            "lines": [{"item_id": setup["item_id"], "quantity_ordered": "5", "unit_price": "20"}],
        },
        headers=headers,
    )

    response = client.get("/api/sales/orders/export", headers=headers)
    rows = _rows(response)
    assert rows[0] == ["Reference", "Customer", "Status", "SKU", "Ordered", "Shipped", "Unit Price"]
    assert rows[1] == ["SO-EXPORT-1", "Bracket Buyers", "draft", "RM-001", "5.0000", "0.0000", "20.0000"]


def test_export_production_orders(client, setup):
    headers = setup["headers"]
    bracket_id = client.post(
        "/api/inventory/items",
        json={"sku": "FG-BRACKET", "name": "Steel Bracket", "item_type": "finished_good", "uom": "EA"},
        headers=headers,
    ).json()["id"]
    bom = client.post(
        "/api/production/boms",
        json={
            "output_item_id": bracket_id,
            "name": "Bracket BOM",
            "components": [{"component_item_id": setup["item_id"], "quantity_per_unit": "2"}],
        },
        headers=headers,
    ).json()
    client.post(
        "/api/production/orders",
        json={"plant_id": setup["plant_id"], "bom_id": bom["id"], "quantity_planned": "5"},
        headers=headers,
    )

    response = client.get("/api/production/orders/export", headers=headers)
    rows = _rows(response)
    assert rows[0] == ["Order ID", "Output SKU", "Status", "Planned", "Completed", "Created"]
    assert rows[1][1] == "FG-BRACKET"
    assert rows[1][2] == "planned"
    assert rows[1][3] == "5.0000"


def test_export_scoped_to_tenant(client, setup):
    other = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Other Co",
            "tenant_slug": "other-co",
            "admin_email": "admin@other.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Other Admin",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    response = client.get("/api/inventory/items/export", headers=other_headers)
    rows = _rows(response)
    assert len(rows) == 1  # header only, no items from the other tenant
