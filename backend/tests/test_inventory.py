import pytest


@pytest.fixture()
def auth_headers_and_plant(client):
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
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    company = client.post("/api/org/companies", json={"name": "Acme East", "code": "ACME-E"}, headers=headers)
    company_id = company.json()["id"]

    plant = client.post(
        "/api/org/plants",
        json={"company_id": company_id, "name": "Plant 1", "code": "P1"},
        headers=headers,
    )
    plant_id = plant.json()["id"]

    return headers, plant_id


def _create_item(client, headers, sku="RM-001"):
    return client.post(
        "/api/inventory/items",
        json={"sku": sku, "name": "Steel Coil", "item_type": "raw_material", "uom": "KG"},
        headers=headers,
    )


def test_create_and_list_items(client, auth_headers_and_plant):
    headers, _ = auth_headers_and_plant
    response = _create_item(client, headers)
    assert response.status_code == 201
    assert response.json()["sku"] == "RM-001"

    listing = client.get("/api/inventory/items", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_duplicate_sku_rejected(client, auth_headers_and_plant):
    headers, _ = auth_headers_and_plant
    _create_item(client, headers)
    response = _create_item(client, headers)
    assert response.status_code == 409


def test_receipt_movement_increases_balance(client, auth_headers_and_plant):
    headers, plant_id = auth_headers_and_plant
    item_id = _create_item(client, headers).json()["id"]

    response = client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "receipt", "quantity": "100"},
        headers=headers,
    )
    assert response.status_code == 201

    balances = client.get("/api/inventory/balances", headers=headers).json()
    assert len(balances) == 1
    assert balances[0]["quantity_on_hand"] == "100.0000"


def test_issue_movement_decreases_balance(client, auth_headers_and_plant):
    headers, plant_id = auth_headers_and_plant
    item_id = _create_item(client, headers).json()["id"]

    client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "receipt", "quantity": "100"},
        headers=headers,
    )
    response = client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "issue", "quantity": "40"},
        headers=headers,
    )
    assert response.status_code == 201

    balances = client.get("/api/inventory/balances", headers=headers).json()
    assert balances[0]["quantity_on_hand"] == "60.0000"


def test_issue_beyond_on_hand_rejected(client, auth_headers_and_plant):
    headers, plant_id = auth_headers_and_plant
    item_id = _create_item(client, headers).json()["id"]

    response = client.post(
        "/api/inventory/movements",
        json={"plant_id": plant_id, "item_id": item_id, "movement_type": "issue", "quantity": "5"},
        headers=headers,
    )
    assert response.status_code == 422


def test_movements_require_authentication(client, auth_headers_and_plant):
    _, plant_id = auth_headers_and_plant
    response = client.get("/api/inventory/movements")
    assert response.status_code == 401


def test_item_from_other_tenant_is_not_visible(client, auth_headers_and_plant):
    headers, plant_id = auth_headers_and_plant
    item_id = _create_item(client, headers).json()["id"]

    other_register = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Globex",
            "tenant_slug": "globex",
            "admin_email": "admin@globex.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Gary Globex",
        },
    )
    other_headers = {"Authorization": f"Bearer {other_register.json()['access_token']}"}

    response = client.get(f"/api/inventory/items/{item_id}", headers=other_headers)
    assert response.status_code == 404
