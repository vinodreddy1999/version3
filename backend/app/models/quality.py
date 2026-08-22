import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.inventory import Item


class InspectionResult(str, enum.Enum):
    pass_ = "pass"
    fail = "fail"


class DefectSeverity(str, enum.Enum):
    minor = "minor"
    major = "major"
    critical = "critical"


class DefectStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class Inspection(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "inspections"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    inspected_quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    result: Mapped[InspectionResult] = mapped_column(Enum(InspectionResult), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    inspector_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    item: Mapped["Item"] = relationship()
    defects: Mapped[list["Defect"]] = relationship(back_populates="inspection", cascade="all, delete-orphan")


class Defect(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "defects"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    inspection_id: Mapped[str] = mapped_column(ForeignKey("inspections.id"), nullable=False)
    defect_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[DefectSeverity] = mapped_column(Enum(DefectSeverity), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[DefectStatus] = mapped_column(Enum(DefectStatus), nullable=False, default=DefectStatus.open)

    inspection: Mapped["Inspection"] = relationship(back_populates="defects")
