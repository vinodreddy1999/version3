import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.inventory import Item


class ProductionOrderStatus(str, enum.Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class WorkCenter(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "work_centers"
    __table_args__ = (UniqueConstraint("plant_id", "code", name="uq_work_center_plant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity_per_hour: Mapped[float | None] = mapped_column(Numeric(14, 4))


class BillOfMaterial(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bills_of_material"
    __table_args__ = (
        UniqueConstraint("tenant_id", "output_item_id", "version", name="uq_bom_tenant_output_version"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    output_item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    components: Mapped[list["BOMComponent"]] = relationship(back_populates="bom", cascade="all, delete-orphan")


class BOMComponent(UUIDPKMixin, Base):
    __tablename__ = "bom_components"
    __table_args__ = (UniqueConstraint("bom_id", "component_item_id", name="uq_bom_component"),)

    bom_id: Mapped[str] = mapped_column(ForeignKey("bills_of_material.id"), nullable=False)
    component_item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity_per_unit: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)

    bom: Mapped["BillOfMaterial"] = relationship(back_populates="components")
    component_item: Mapped["Item"] = relationship()


class ProductionOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "production_orders"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    bom_id: Mapped[str] = mapped_column(ForeignKey("bills_of_material.id"), nullable=False)
    work_center_id: Mapped[str | None] = mapped_column(ForeignKey("work_centers.id"))
    quantity_planned: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_completed: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    status: Mapped[ProductionOrderStatus] = mapped_column(
        Enum(ProductionOrderStatus), nullable=False, default=ProductionOrderStatus.planned
    )
    reference: Mapped[str | None] = mapped_column(String(200))
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    bom: Mapped["BillOfMaterial"] = relationship()
