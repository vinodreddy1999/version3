import enum

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.inventory import Item


class SalesOrderStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    partially_shipped = "partially_shipped"
    shipped = "shipped"
    cancelled = "cancelled"


class Customer(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_customer_tenant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class SalesOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sales_orders"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[SalesOrderStatus] = mapped_column(
        Enum(SalesOrderStatus), nullable=False, default=SalesOrderStatus.draft
    )
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    lines: Mapped[list["SalesOrderLine"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class SalesOrderLine(UUIDPKMixin, Base):
    __tablename__ = "sales_order_lines"

    order_id: Mapped[str] = mapped_column(ForeignKey("sales_orders.id"), nullable=False)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity_ordered: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    quantity_shipped: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)

    order: Mapped["SalesOrder"] = relationship(back_populates="lines")
    item: Mapped["Item"] = relationship()

    @property
    def item_sku(self) -> str:
        return self.item.sku
