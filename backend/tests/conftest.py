import os
import tempfile

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ATTACHMENTS_DIR", tempfile.mkdtemp(prefix="metam_test_attachments_"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db_session
from app.core.db import Base
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_tenant_headers(client, slug: str = "acme") -> dict[str, str]:
    """Registers a fresh tenant + admin user, returning Bearer auth headers."""
    response = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Acme Manufacturing",
            "tenant_slug": slug,
            "admin_email": "admin@acme.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Ada Admin",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return register_tenant_headers(client)


@pytest.fixture()
def headers(client):
    return register_tenant_headers(client)


def other_tenant_headers(client) -> dict[str, str]:
    """Registers a second ('Globex') tenant + admin, for cross-tenant isolation tests."""
    response = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Globex",
            "tenant_slug": "globex",
            "admin_email": "admin@globex.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Gary Globex",
        },
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
