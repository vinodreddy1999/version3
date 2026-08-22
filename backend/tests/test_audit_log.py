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


def test_registration_is_audited(client, admin_headers):
    response = client.get("/api/admin/audit-log", headers=admin_headers)
    assert response.status_code == 200
    actions = [e["action"] for e in response.json()]
    assert "tenant.registered" in actions


def test_login_is_audited(client, admin_headers):
    client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "SuperSecret123!", "tenant_slug": "acme"},
    )
    response = client.get("/api/admin/audit-log", headers=admin_headers)
    logins = [e for e in response.json() if e["action"] == "user.login"]
    assert len(logins) == 1
    assert logins[0]["actor_email"] == "admin@acme.example.com"


def test_role_lifecycle_is_audited(client, admin_headers):
    role = client.post(
        "/api/admin/roles",
        json={"name": "Clerk", "permission_codes": ["inventory:read"]},
        headers=admin_headers,
    ).json()
    client.patch(
        f"/api/admin/roles/{role['id']}",
        json={"permission_codes": ["inventory:read", "inventory:write"]},
        headers=admin_headers,
    )
    client.delete(f"/api/admin/roles/{role['id']}", headers=admin_headers)

    response = client.get("/api/admin/audit-log", headers=admin_headers)
    actions = [e["action"] for e in response.json()]
    assert "role.created" in actions
    assert "role.updated" in actions
    assert "role.deleted" in actions


def test_user_lifecycle_is_audited(client, admin_headers):
    created = client.post(
        "/api/admin/users",
        json={"email": "clerk@acme.example.com", "full_name": "Carla Clerk", "password": "SuperSecret123!"},
        headers=admin_headers,
    ).json()
    client.patch(f"/api/admin/users/{created['id']}", json={"is_active": False}, headers=admin_headers)

    response = client.get("/api/admin/audit-log", headers=admin_headers)
    entries = response.json()
    created_entries = [e for e in entries if e["action"] == "user.created"]
    updated_entries = [e for e in entries if e["action"] == "user.updated"]
    assert len(created_entries) == 1
    assert "clerk@acme.example.com" in created_entries[0]["summary"]
    assert len(updated_entries) == 1
    assert "deactivated" in updated_entries[0]["summary"]


def test_audit_log_requires_permission(client, admin_headers):
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

    response = client.get("/api/admin/audit-log", headers=clerk_headers)
    assert response.status_code == 403


def test_audit_log_isolated_per_tenant(client, admin_headers):
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

    acme_log = client.get("/api/admin/audit-log", headers=admin_headers).json()
    globex_log = client.get("/api/admin/audit-log", headers=other_headers).json()

    assert all("Acme" not in e["summary"] or "Globex" not in e["summary"] for e in acme_log)
    assert not any(e["actor_email"] == "admin@globex.example.com" for e in acme_log)
    assert not any(e["actor_email"] == "admin@acme.example.com" for e in globex_log)


def test_audit_log_ordered_most_recent_first(client, admin_headers):
    client.post("/api/admin/roles", json={"name": "Role A", "permission_codes": []}, headers=admin_headers)
    client.post("/api/admin/roles", json={"name": "Role B", "permission_codes": []}, headers=admin_headers)

    entries = client.get("/api/admin/audit-log", headers=admin_headers).json()
    role_created = [e for e in entries if e["action"] == "role.created"]
    assert role_created[0]["summary"].endswith("permissions: none") and "Role B" in role_created[0]["summary"]
    assert "Role A" in role_created[1]["summary"]
