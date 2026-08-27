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


def create_plant(client, headers: dict[str, str]) -> str:
    """Creates a company + plant ('Acme East' / 'Plant 1'), returning the plant id."""
    company_id = client.post(
        "/api/org/companies", json={"name": "Acme East", "code": "ACME-E"}, headers=headers
    ).json()["id"]
    return client.post(
        "/api/org/plants", json={"company_id": company_id, "name": "Plant 1", "code": "P1"}, headers=headers
    ).json()["id"]


def create_item(client, headers: dict[str, str]) -> str:
    """Creates a raw material item ('RM-001' / 'Steel Coil'), returning its id."""
    return client.post(
        "/api/inventory/items",
        json={"sku": "RM-001", "name": "Steel Coil", "item_type": "raw_material", "uom": "KG"},
        headers=headers,
    ).json()["id"]


def create_supplier(client, headers: dict[str, str]) -> str:
    """Creates a supplier ('SteelCo' / 'SUP-1'), returning its id."""
    return client.post(
        "/api/procurement/suppliers", json={"name": "SteelCo", "code": "SUP-1"}, headers=headers
    ).json()["id"]


def create_customer(client, headers: dict[str, str]) -> str:
    """Creates a customer ('Bracket Buyers' / 'CUST-1'), returning its id."""
    return client.post(
        "/api/sales/customers", json={"name": "Bracket Buyers", "code": "CUST-1"}, headers=headers
    ).json()["id"]
