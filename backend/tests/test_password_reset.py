import re

import pytest

from app.core.email import get_email_backend
from app.main import app


class RecordingEmailBackend:
    def __init__(self):
        self.sent: list[dict] = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


@pytest.fixture()
def email_backend():
    backend = RecordingEmailBackend()
    app.dependency_overrides[get_email_backend] = lambda: backend
    yield backend
    del app.dependency_overrides[get_email_backend]


def _register(client):
    return client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Acme Manufacturing",
            "tenant_slug": "acme",
            "admin_email": "admin@acme.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Ada Admin",
        },
    )


def _extract_token(email_body: str) -> str:
    match = re.search(r"token=([\w-]+)", email_body)
    assert match, f"no reset token found in email body: {email_body}"
    return match.group(1)


def test_forgot_password_sends_email_with_reset_link(client, email_backend):
    _register(client)
    response = client.post(
        "/api/auth/forgot-password", json={"email": "admin@acme.example.com", "tenant_slug": "acme"}
    )
    assert response.status_code == 200
    assert len(email_backend.sent) == 1
    assert email_backend.sent[0]["to"] == "admin@acme.example.com"
    assert "token=" in email_backend.sent[0]["body"]


def test_forgot_password_is_generic_for_unknown_email(client, email_backend):
    _register(client)
    response = client.post(
        "/api/auth/forgot-password", json={"email": "nobody@acme.example.com", "tenant_slug": "acme"}
    )
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["detail"]
    assert len(email_backend.sent) == 0


def test_forgot_password_is_generic_for_unknown_tenant(client, email_backend):
    response = client.post(
        "/api/auth/forgot-password", json={"email": "admin@acme.example.com", "tenant_slug": "does-not-exist"}
    )
    assert response.status_code == 200
    assert len(email_backend.sent) == 0


def test_reset_password_with_valid_token_changes_password(client, email_backend):
    _register(client)
    client.post("/api/auth/forgot-password", json={"email": "admin@acme.example.com", "tenant_slug": "acme"})
    token = _extract_token(email_backend.sent[0]["body"])

    response = client.post("/api/auth/reset-password", json={"token": token, "new_password": "BrandNewPass123!"})
    assert response.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "SuperSecret123!", "tenant_slug": "acme"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "BrandNewPass123!", "tenant_slug": "acme"},
    )
    assert new_login.status_code == 200


def test_reset_token_cannot_be_reused(client, email_backend):
    _register(client)
    client.post("/api/auth/forgot-password", json={"email": "admin@acme.example.com", "tenant_slug": "acme"})
    token = _extract_token(email_backend.sent[0]["body"])

    first = client.post("/api/auth/reset-password", json={"token": token, "new_password": "BrandNewPass123!"})
    assert first.status_code == 200

    second = client.post("/api/auth/reset-password", json={"token": token, "new_password": "AnotherPass456!"})
    assert second.status_code == 422


def test_reset_password_with_garbage_token_rejected(client):
    response = client.post("/api/auth/reset-password", json={"token": "not-a-real-token", "new_password": "Whatever123!"})
    assert response.status_code == 422


def test_reset_password_and_forgot_password_are_audited(client, email_backend):
    register = _register(client)
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    client.post("/api/auth/forgot-password", json={"email": "admin@acme.example.com", "tenant_slug": "acme"})
    token = _extract_token(email_backend.sent[0]["body"])
    client.post("/api/auth/reset-password", json={"token": token, "new_password": "BrandNewPass123!"})

    log = client.post(
        "/api/auth/login",
        json={"email": "admin@acme.example.com", "password": "BrandNewPass123!", "tenant_slug": "acme"},
    ).json()
    audit_headers = {"Authorization": f"Bearer {log['access_token']}"}
    entries = client.get("/api/admin/audit-log", headers=audit_headers).json()
    actions = [e["action"] for e in entries]
    assert "user.password_reset_requested" in actions
    assert "user.password_reset" in actions
