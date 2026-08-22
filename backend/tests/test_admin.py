import pytest


@pytest.fixture()
def admin_headers(client):
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


def test_admin_role_gets_all_permissions_on_registration(client, admin_headers):
    roles = client.get("/api/admin/roles", headers=admin_headers).json()
    assert len(roles) == 1
    assert roles[0]["name"] == "Admin"
    assert roles[0]["is_system"] is True
    assert "inventory:write" in roles[0]["permission_codes"]
    assert "admin:manage_users" in roles[0]["permission_codes"]


def test_permission_catalog_is_listable(client, admin_headers):
    response = client.get("/api/admin/permissions", headers=admin_headers)
    assert response.status_code == 200
    codes = {p["code"] for p in response.json()}
    assert "inventory:read" in codes
    assert "admin:manage_roles" in codes


def test_create_custom_role_with_subset_of_permissions(client, admin_headers):
    response = client.post(
        "/api/admin/roles",
        json={"name": "Warehouse Clerk", "permission_codes": ["inventory:read", "warehouse:write"]},
        headers=admin_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["is_system"] is False
    assert set(body["permission_codes"]) == {"inventory:read", "warehouse:write"}


def test_create_role_with_unknown_permission_rejected(client, admin_headers):
    response = client.post(
        "/api/admin/roles",
        json={"name": "Bad Role", "permission_codes": ["not:a:real:permission"]},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_duplicate_role_name_rejected(client, admin_headers):
    client.post("/api/admin/roles", json={"name": "Clerk", "permission_codes": []}, headers=admin_headers)
    response = client.post("/api/admin/roles", json={"name": "Clerk", "permission_codes": []}, headers=admin_headers)
    assert response.status_code == 409


def test_system_admin_role_cannot_be_deleted(client, admin_headers):
    roles = client.get("/api/admin/roles", headers=admin_headers).json()
    admin_role_id = roles[0]["id"]
    response = client.delete(f"/api/admin/roles/{admin_role_id}", headers=admin_headers)
    assert response.status_code == 409


def test_create_and_update_user_with_role_assignment(client, admin_headers):
    role = client.post(
        "/api/admin/roles", json={"name": "Clerk", "permission_codes": ["inventory:read"]}, headers=admin_headers
    ).json()

    created = client.post(
        "/api/admin/users",
        json={
            "email": "clerk@acme.example.com",
            "full_name": "Carla Clerk",
            "password": "AnotherSecret123!",
            "role_ids": [role["id"]],
        },
        headers=admin_headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["role_names"] == ["Clerk"]
    assert body["is_superuser"] is False

    login = client.post(
        "/api/auth/login",
        json={"email": "clerk@acme.example.com", "password": "AnotherSecret123!", "tenant_slug": "acme"},
    )
    assert login.status_code == 200

    updated = client.patch(
        f"/api/admin/users/{body['id']}", json={"is_active": False}, headers=admin_headers
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    blocked_login = client.post(
        "/api/auth/login",
        json={"email": "clerk@acme.example.com", "password": "AnotherSecret123!", "tenant_slug": "acme"},
    )
    assert blocked_login.status_code == 401


def test_cannot_deactivate_own_account(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    response = client.patch(f"/api/admin/users/{me['id']}", json={"is_active": False}, headers=admin_headers)
    assert response.status_code == 422


def test_duplicate_user_email_rejected(client, admin_headers):
    client.post(
        "/api/admin/users",
        json={"email": "dup@acme.example.com", "full_name": "Dup One", "password": "SuperSecret123!"},
        headers=admin_headers,
    )
    response = client.post(
        "/api/admin/users",
        json={"email": "dup@acme.example.com", "full_name": "Dup Two", "password": "SuperSecret123!"},
        headers=admin_headers,
    )
    assert response.status_code == 409


def test_non_admin_user_cannot_manage_users(client, admin_headers):
    role = client.post(
        "/api/admin/roles", json={"name": "Clerk", "permission_codes": ["inventory:read"]}, headers=admin_headers
    ).json()
    clerk = client.post(
        "/api/admin/users",
        json={
            "email": "clerk2@acme.example.com",
            "full_name": "Carla Clerk",
            "password": "AnotherSecret123!",
            "role_ids": [role["id"]],
        },
        headers=admin_headers,
    ).json()
    clerk_login = client.post(
        "/api/auth/login",
        json={"email": "clerk2@acme.example.com", "password": "AnotherSecret123!", "tenant_slug": "acme"},
    ).json()
    clerk_headers = {"Authorization": f"Bearer {clerk_login['access_token']}"}

    response = client.get("/api/admin/users", headers=clerk_headers)
    assert response.status_code == 403


def test_admin_endpoints_isolated_per_tenant(client, admin_headers):
    other = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Globex",
            "tenant_slug": "globex",
            "admin_email": "admin@globex.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Gary Globex",
        },
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    acme_users = client.get("/api/admin/users", headers=admin_headers).json()
    globex_users = client.get("/api/admin/users", headers=other_headers).json()
    assert len(acme_users) == 1
    assert len(globex_users) == 1
    assert acme_users[0]["email"] != globex_users[0]["email"]
