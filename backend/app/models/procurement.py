import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.inventory import Item


class PurchaseOrderStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class Supplier(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_supplier_tenant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class PurchaseOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus), nullable=False, default=PurchaseOrderStatus.draft
    )
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class PurchaseOrderLine(UUIDPKMixin, Base):
    __tablename__ = "purchase_order_lines"

    order_id: Mapped[str] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)

    order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")
    item: Mapped["Item"] = relationship()

    @property
    def item_sku(self) -> str:
        return self.item.sku
