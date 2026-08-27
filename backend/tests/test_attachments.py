import pytest

from app.core.config import settings
from conftest import create_item, create_plant, create_supplier, register_tenant_headers


@pytest.fixture()
def setup(client):
    headers = register_tenant_headers(client)
    plant_id = create_plant(client, headers)
    item_id = create_item(client, headers)
    inspection_id = client.post(
        "/api/quality/inspections",
        json={"plant_id": plant_id, "item_id": item_id, "inspected_quantity": "10"},
        headers=headers,
    ).json()["id"]
    supplier_id = create_supplier(client, headers)
    po_id = client.post(
        "/api/procurement/orders",
        json={
            "plant_id": plant_id,
            "supplier_id": supplier_id,
            "lines": [{"item_id": item_id, "quantity_ordered": "5"}],
        },
        headers=headers,
    ).json()["id"]

    return {"headers": headers, "inspection_id": inspection_id, "po_id": po_id}


def test_upload_and_list_attachment_on_inspection(client, setup):
    headers = setup["headers"]
    upload = client.post(
        "/api/attachments",
        data={"entity_type": "inspection", "entity_id": setup["inspection_id"]},
        files={"file": ("report.pdf", b"%PDF-1.4 fake contents", "application/pdf")},
        headers=headers,
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["filename"] == "report.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["entity_type"] == "inspection"
    assert body["entity_id"] == setup["inspection_id"]

    listing = client.get(
        "/api/attachments",
        params={"entity_type": "inspection", "entity_id": setup["inspection_id"]},
        headers=headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == body["id"]


def test_upload_and_download_attachment_on_purchase_order(client, setup):
    headers = setup["headers"]
    upload = client.post(
        "/api/attachments",
        data={"entity_type": "purchase_order", "entity_id": setup["po_id"]},
        files={"file": ("quote.txt", b"vendor quote contents", "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201
    attachment_id = upload.json()["id"]

    download = client.get(f"/api/attachments/{attachment_id}/download", headers=headers)
    assert download.status_code == 200
    assert download.content == b"vendor quote contents"
    assert "quote.txt" in download.headers["content-disposition"]


def test_upload_rejects_unsupported_entity_type(client, setup):
    headers = setup["headers"]
    response = client.post(
        "/api/attachments",
        data={"entity_type": "sales_order", "entity_id": "whatever"},
        files={"file": ("a.txt", b"data", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 422


def test_upload_rejects_entity_from_another_tenant(client, setup):
    other = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Other Co",
            "tenant_slug": "other-co",
            "admin_email": "admin@other.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Other Admin",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    response = client.post(
        "/api/attachments",
        data={"entity_type": "inspection", "entity_id": setup["inspection_id"]},
        files={"file": ("a.txt", b"data", "text/plain")},
        headers=other_headers,
    )
    assert response.status_code == 404


def test_attachment_not_visible_to_another_tenant(client, setup):
    headers = setup["headers"]
    upload = client.post(
        "/api/attachments",
        data={"entity_type": "inspection", "entity_id": setup["inspection_id"]},
        files={"file": ("a.txt", b"data", "text/plain")},
        headers=headers,
    ).json()

    other = client.post(
        "/api/auth/register-tenant",
        json={
            "tenant_name": "Other Co",
            "tenant_slug": "other-co-2",
            "admin_email": "admin@other2.example.com",
            "admin_password": "SuperSecret123!",
            "admin_full_name": "Other Admin",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    response = client.get(f"/api/attachments/{upload['id']}/download", headers=other_headers)
    assert response.status_code == 404


def test_upload_rejects_oversized_file(client, setup, monkeypatch):
    monkeypatch.setattr(settings, "max_attachment_size_bytes", 10)
    headers = setup["headers"]
    response = client.post(
        "/api/attachments",
        data={"entity_type": "inspection", "entity_id": setup["inspection_id"]},
        files={"file": ("a.txt", b"this is definitely more than ten bytes", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 413
