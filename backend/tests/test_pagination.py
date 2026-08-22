import pytest


@pytest.fixture()
def headers(client):
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
    return {"Authorization": f"Bearer {register.json()['access_token']}"}


def test_items_list_respects_limit_and_offset(client, headers):
    for i in range(5):
        client.post(
            "/api/inventory/items",
            json={"sku": f"SKU-{i}", "name": f"Item {i}", "item_type": "raw_material"},
            headers=headers,
        )

    first_page = client.get("/api/inventory/items", params={"limit": 2, "offset": 0}, headers=headers)
    assert first_page.status_code == 200
    assert len(first_page.json()) == 2
    assert first_page.headers["X-Total-Count"] == "5"

    second_page = client.get("/api/inventory/items", params={"limit": 2, "offset": 2}, headers=headers)
    assert len(second_page.json()) == 2
    assert {i["sku"] for i in first_page.json()} != {i["sku"] for i in second_page.json()}

    last_page = client.get("/api/inventory/items", params={"limit": 2, "offset": 4}, headers=headers)
    assert len(last_page.json()) == 1


def test_admin_users_list_respects_pagination(client, headers):
    for i in range(3):
        client.post(
            "/api/admin/users",
            json={"email": f"user{i}@acme.example.com", "full_name": f"User {i}", "password": "SuperSecret123!"},
            headers=headers,
        )

    # 3 created + the tenant admin itself = 4
    response = client.get("/api/admin/users", params={"limit": 2}, headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "4"


def test_limit_is_capped_at_maximum(client, headers):
    response = client.get("/api/inventory/items", params={"limit": 5000}, headers=headers)
    assert response.status_code == 422


def test_default_limit_is_generous_enough_for_dropdowns(client, headers):
    for i in range(60):
        client.post(
            "/api/inventory/items",
            json={"sku": f"BULK-{i}", "name": f"Bulk item {i}", "item_type": "consumable"},
            headers=headers,
        )
    response = client.get("/api/inventory/items", headers=headers)
    assert len(response.json()) == 60
    assert response.headers["X-Total-Count"] == "60"
