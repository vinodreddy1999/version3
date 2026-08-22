from pydantic import BaseModel, Field

from app.models.maintenance import AssetStatus, WorkOrderPriority, WorkOrderStatus, WorkOrderType


class AssetCreate(BaseModel):
    plant_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)


class AssetOut(BaseModel):
    id: str
    plant_id: str
    name: str
    code: str
    status: AssetStatus
    is_active: bool

    model_config = {"from_attributes": True}


class WorkOrderCreate(BaseModel):
    plant_id: str
    asset_id: str
    work_order_type: WorkOrderType
    priority: WorkOrderPriority = WorkOrderPriority.medium
    description: str | None = None


class WorkOrderOut(BaseModel):
    id: str
    plant_id: str
    asset_id: str
    work_order_type: WorkOrderType
    priority: WorkOrderPriority
    status: WorkOrderStatus
    description: str | None

    model_config = {"from_attributes": True}
