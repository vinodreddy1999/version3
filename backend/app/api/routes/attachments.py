import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.api.routes.procurement import _get_owned_po
from app.api.routes.quality import _get_owned_inspection
from app.core.config import settings
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment import AttachmentOut

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

# Which entities attachments can be linked to, and how to verify the caller's
# tenant actually owns the entity_id they're attaching to.
_OWNERSHIP_CHECKS = {
    "inspection": _get_owned_inspection,
    "purchase_order": _get_owned_po,
}


def _assert_entity_owned(db: Session, user: User, entity_type: str, entity_id: str) -> None:
    check = _OWNERSHIP_CHECKS.get(entity_type)
    if check is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Unsupported entity_type '{entity_type}'",
        )
    check(db, user, entity_id)


@router.post("", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    _assert_entity_owned(db, user, entity_type, entity_id)

    contents = await file.read()
    if len(contents) > settings.max_attachment_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="File exceeds maximum allowed size"
        )

    tenant_dir = Path(settings.attachments_dir) / user.tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)

    # Strip any path components from the client-supplied filename before using
    # it, and namespace the file on disk with a UUID so uploads never collide
    # or overwrite each other.
    original_name = os.path.basename(file.filename or "upload")
    storage_path = tenant_dir / f"{uuid.uuid4()}_{original_name}"
    storage_path.write_bytes(contents)

    attachment = Attachment(
        tenant_id=user.tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        filename=original_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_path=str(storage_path),
        uploaded_by_user_id=user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("", response_model=list[AttachmentOut])
def list_attachments(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db_session),
    user: User = Depends(get_current_user),
):
    return (
        db.query(Attachment)
        .filter(
            Attachment.tenant_id == user.tenant_id,
            Attachment.entity_type == entity_type,
            Attachment.entity_id == entity_id,
        )
        .order_by(Attachment.created_at.desc())
        .all()
    )


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: str, db: Session = Depends(get_db_session), user: User = Depends(get_current_user)
):
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or attachment.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    if not os.path.exists(attachment.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing")
    return FileResponse(attachment.storage_path, media_type=attachment.content_type, filename=attachment.filename)
