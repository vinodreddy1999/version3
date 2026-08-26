import pytest

from conftest import other_tenant_headers


@pytest.fixture()
def clerk(client, admin_headers):
    role = client.post(
        "/api/admin/roles", json={"name": "Clerk", "permission_codes": ["inventory:read"]}, headers=admin_headers
    ).json()
    return client.post(
        "/api/admin/users",
        json={
            "email": "clerk@acme.example.com",
            "full_name": "Carla Clerk",
            "password": "AnotherSecret123!",
            "role_ids": [role["id"]],
        },
        headers=admin_headers,
    ).json()


def test_superuser_can_impersonate_a_user(client, admin_headers, clerk):
    response = client.post(f"/api/admin/users/{clerk['id']}/impersonate", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert "refresh_token" not in body
    impersonated_headers = {"Authorization": f"Bearer {body['access_token']}"}

    me = client.get("/api/auth/me", headers=impersonated_headers).json()
    assert me["id"] == clerk["id"]
    assert me["email"] == "clerk@acme.example.com"
    assert me["permissions"] == ["inventory:read"]
    assert me["impersonated_by"]["email"] == "admin@acme.example.com"


def test_impersonated_session_is_scoped_like_the_real_user(client, admin_headers, clerk):
    impersonate = client.post(f"/api/admin/users/{clerk['id']}/impersonate", headers=admin_headers)
    impersonated_headers = {"Authorization": f"Bearer {impersonate.json()['access_token']}"}

    # Clerk only has inventory:read, not admin:manage_users.
    response = client.get("/api/admin/users", headers=impersonated_headers)
    assert response.status_code == 403


def test_impersonation_records_an_audit_entry(client, admin_headers, clerk):
    client.post(f"/api/admin/users/{clerk['id']}/impersonate", headers=admin_headers)
    entries = client.get("/api/admin/audit-log", headers=admin_headers).json()
    impersonate_entries = [e for e in entries if e["action"] == "user.impersonate_start"]
    assert len(impersonate_entries) == 1
    assert "started impersonating" in impersonate_entries[0]["summary"]


def test_non_superuser_cannot_impersonate(client, admin_headers, clerk):
    login = client.post(
        "/api/auth/login",
        json={"email": "clerk@acme.example.com", "password": "AnotherSecret123!", "tenant_slug": "acme"},
    ).json()
    clerk_headers = {"Authorization": f"Bearer {login['access_token']}"}

    other = client.post(
        "/api/admin/users",
        json={"email": "other@acme.example.com", "full_name": "Other Person", "password": "SuperSecret123!"},
        headers=admin_headers,
    ).json()

    response = client.post(f"/api/admin/users/{other['id']}/impersonate", headers=clerk_headers)
    assert response.status_code == 403


def test_cannot_impersonate_self(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    response = client.post(f"/api/admin/users/{me['id']}/impersonate", headers=admin_headers)
    assert response.status_code == 422


def test_cannot_impersonate_inactive_user(client, admin_headers, clerk):
    client.patch(f"/api/admin/users/{clerk['id']}", json={"is_active": False}, headers=admin_headers)
    response = client.post(f"/api/admin/users/{clerk['id']}/impersonate", headers=admin_headers)
    assert response.status_code == 409


def test_cannot_impersonate_user_in_another_tenant(client, admin_headers, clerk):
    other_headers = other_tenant_headers(client)

    response = client.post(f"/api/admin/users/{clerk['id']}/impersonate", headers=other_headers)
    assert response.status_code == 404


def test_me_has_no_impersonated_by_for_normal_session(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers).json()
    assert me["impersonated_by"] is None
