def _register(client, slug="acme"):
    return client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Acme Manufacturing",
            "tenant_slug": slug,
            "admin_email": "admin@acme.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Ada Admin",
        },
    )


def test_register_tenant_creates_admin_and_returns_tokens(client):
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_register_tenant_rejects_duplicate_slug(client):
    _register(client)
    response = _register(client)
    assert response.status_code == 409


def test_login_with_correct_credentials_succeeds(client):
    _register(client)
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "SuperSecret123!", "tenant_slug": "acme"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    _register(client)
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "wrong-password", "tenant_slug": "acme"},
    )
    assert response.status_code == 401


def test_login_with_unknown_tenant_fails(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "SuperSecret123!", "tenant_slug": "does-not-exist"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    tokens = _register(client).json()
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@acme.example.com"
    assert body["is_superuser"] is True
    assert "Admin" in body["roles"]


def test_refresh_issues_new_access_token(client):
    tokens = _register(client).json()
    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_rejects_access_token_used_as_refresh_token(client):
    tokens = _register(client).json()
    response = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert response.status_code == 401


def test_me_rejects_tampered_token(client):
    tokens = _register(client).json()
    tampered = tokens["access_token"][:-1] + ("A" if tokens["access_token"][-1] != "A" else "B")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401
