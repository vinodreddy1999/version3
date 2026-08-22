from datetime import datetime

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}
