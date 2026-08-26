from datetime import datetime

from app.schemas.base import ORMModel


class AttachmentOut(ORMModel):
    id: str
    entity_type: str
    entity_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
