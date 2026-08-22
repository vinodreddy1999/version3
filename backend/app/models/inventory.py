import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class ItemType(str, enum.Enum):
    raw_material = "raw_material"
    work_in_progress = "work_in_progress"
    finished_good = "finished_good"
    consumable = "consumable"


class MovementType(str, enum.Enum):
    receipt = "receipt"
    issue = "issue"
    adjustment = "adjustment"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"


class Item(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "items"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_item_tenant_sku"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    item_type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False)
    uom: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    reorder_point: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class StockBalance(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "stock_balances"
    __table_args__ = (UniqueConstraint("plant_id", "item_id", name="uq_balance_plant_item"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    quantity_reserved: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)

    item: Mapped["Item"] = relationship()


class StockMovement(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "stock_movements"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    item: Mapped["Item"] = relationship()
