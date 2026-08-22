import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.inventory import Item


class ZoneType(str, enum.Enum):
    receiving = "receiving"
    storage = "storage"
    picking = "picking"
    shipping = "shipping"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class Warehouse(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("plant_id", "code", name="uq_warehouse_plant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)

    zones: Mapped[list["Zone"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")


class Zone(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("warehouse_id", "code", name="uq_zone_warehouse_code"),)

    warehouse_id: Mapped[str] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(Enum(ZoneType), nullable=False)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="zones")
    bins: Mapped[list["Bin"]] = relationship(back_populates="zone", cascade="all, delete-orphan")


class Bin(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bins"
    __table_args__ = (UniqueConstraint("zone_id", "code", name="uq_bin_zone_code"),)

    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)

    zone: Mapped["Zone"] = relationship(back_populates="bins")


class BinStock(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bin_stock"
    __table_args__ = (UniqueConstraint("bin_id", "item_id", name="uq_bin_stock_bin_item"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    bin_id: Mapped[str] = mapped_column(ForeignKey("bins.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)

    bin: Mapped["Bin"] = relationship()
    item: Mapped["Item"] = relationship()


class PutawayTask(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "putaway_tasks"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    destination_bin_id: Mapped[str] = mapped_column(ForeignKey("bins.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)


class PickTask(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "pick_tasks"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    source_bin_id: Mapped[str] = mapped_column(ForeignKey("bins.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.pending)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
