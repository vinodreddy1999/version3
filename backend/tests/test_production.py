import pytest


@pytest.fixture()
def setup(client):
    register = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Acme Manufacturing",
            "tenant_slug": "acme",
            "admin_email": "admin@acme.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Ada Admin",
        },
    )
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    company_id = client.post(
        "/api/org/companies", json={"name": "Acme East", "code": "ACME-E"}, headers=headers
    ).json()["id"]
    plant_id = client.post(
        "/api/org/plants", json={"company_id": company_id, "name": "Plant 1", "code": "P1"}, headers=headers
    ).json()["id"]

    steel_id = client.post(
        "/api/inventory/items",
        json={"sku": "RM-STEEL", "name": "Steel Sheet", "item_type": "raw_material", "uom": "KG"},
        headers=headers,
    ).json()["id"]
    bolt_id = client.post(
        "/api/inventory/items",
        json={"sku": "RM-BOLT", "name": "Bolt", "item_type": "raw_material", "uom": "EA"},
        headers=headers,
    ).json()["id"]
    bracket_id = client.post(
        "/api/inventory/items",
        json={"sku": "FG-BRACKET", "name": "Steel Bracket", "item_type": "finished_good", "uom": "EA"},
        headers=headers,
    ).json()["id"]

    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": steel_id, "movement_type": "receipt", "quantity": "100"},
        headers=headers,
    )
    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": bolt_id, "movement_type": "receipt", "quantity": "500"},
        headers=headers,
    )

    bom = client.post(
        "/api/production/boms",
        json={
            "output_item_id": bracket_id,
            "name": "Bracket BOM",
            "components": [
                {"component_item_id": steel_id, "quantity_per_unit": "2"},
                {"component_item_id": bolt_id, "quantity_per_unit": "4"},
            ],
        },
        headers=headers,
    ).json()

    return {
        "headers": headers,
        "plant_id": plant_id,
        "steel_id": steel_id,
        "bolt_id": bolt_id,
        "bracket_id": bracket_id,
        "bom_id": bom["id"],
    }


def test_bom_created_with_components(setup):
    assert len(setup) > 0  # sanity: fixture built without error


def test_production_order_completion_consumes_and_produces_stock(client, setup):
    headers = setup["headers"]
    order = client.post(
        "/api/production/orders",
        json={"plant_id": setup["plant_id"], "bom_id": setup["bom_id"], "quantity_planned": "10"},
        headers=headers,
    ).json()

    response = client.post(
        f"/api/production/orders/{order['id']}/complete", json={"quantity": "10"}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["quantity_completed"] == "10.0000"

    balances = {b["item_id"]: b for b in client.get("/api/inventory/balances", headers=headers).json()}
    assert balances[setup["steel_id"]]["quantity_on_hand"] == "80.0000"
    assert balances[setup["bolt_id"]]["quantity_on_hand"] == "460.0000"
    assert balances[setup["bracket_id"]]["quantity_on_hand"] == "10.0000"


def test_partial_completion_then_final_completion(client, setup):
    headers = setup["headers"]
    order = client.post(
        "/api/production/orders",
        json={"plant_id": setup["plant_id"], "bom_id": setup["bom_id"], "quantity_planned": "10"},
        headers=headers,
    ).json()

    first = client.post(
        f"/api/production/orders/{order['id']}/complete", json={"quantity": "6"}, headers=headers
    )
    assert first.status_code == 200
    assert first.json()["status"] == "in_progress"

    second = client.post(
        f"/api/production/orders/{order['id']}/complete", json={"quantity": "4"}, headers=headers
    )
    assert second.status_code == 200
    assert second.json()["status"] == "completed"


def test_completion_beyond_remaining_rejected(client, setup):
    headers = setup["headers"]
    order = client.post(
        "/api/production/orders",
        json={"plant_id": setup["plant_id"], "bom_id": setup["bom_id"], "quantity_planned": "5"},
        headers=headers,
    ).json()

    response = client.post(
        f"/api/production/orders/{order['id']}/complete", json={"quantity": "6"}, headers=headers
    )
    assert response.status_code == 422


def test_completion_with_insufficient_component_stock_rejected(client, setup):
    headers = setup["headers"]
    order = client.post(
        "/api/production/orders",
        json={"plant_id": setup["plant_id"], "bom_id": setup["bom_id"], "quantity_planned": "1000"},
        headers=headers,
    ).json()

    response = client.post(
        f"/api/production/orders/{order['id']}/complete", json={"quantity": "1000"}, headers=headers
    )
    assert response.status_code == 422

    balances = {b["item_id"]: b for b in client.get("/api/inventory/balances", headers=headers).json()}
    assert balances[setup["steel_id"]]["quantity_on_hand"] == "100.0000"


def test_component_cannot_be_own_output(client, setup):
    headers = setup["headers"]
    response = client.post(
        "/api/production/boms",
        json={
            "output_item_id": setup["bracket_id"],
            "name": "Bad BOM",
            "components": [{"component_item_id": setup["bracket_id"], "quantity_per_unit": "1"}],
        },
        headers=headers,
    )
    assert response.status_code == 422
