import enum

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class AssetStatus(str, enum.Enum):
    operational = "operational"
    down = "down"
    maintenance = "maintenance"


class WorkOrderType(str, enum.Enum):
    preventive = "preventive"
    corrective = "corrective"
    inspection = "inspection"


class WorkOrderPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class WorkOrderStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Asset(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("plant_id", "code", name="uq_asset_plant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), nullable=False, default=AssetStatus.operational)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class MaintenanceWorkOrder(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "maintenance_work_orders"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(ForeignKey("plants.id"), nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=False)
    work_order_type: Mapped[WorkOrderType] = mapped_column(Enum(WorkOrderType), nullable=False)
    priority: Mapped[WorkOrderPriority] = mapped_column(
        Enum(WorkOrderPriority), nullable=False, default=WorkOrderPriority.medium
    )
    status: Mapped[WorkOrderStatus] = mapped_column(Enum(WorkOrderStatus), nullable=False, default=WorkOrderStatus.open)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    asset: Mapped["Asset"] = relationship()
