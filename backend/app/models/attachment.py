from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class Attachment(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("ix_attachments_entity", "tenant_id", "entity_type", "entity_id"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
