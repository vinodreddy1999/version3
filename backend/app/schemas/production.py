from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.production import ProductionOrderStatus


class WorkCenterCreate(BaseModel):
    plant_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    capacity_per_hour: Decimal | None = None


class WorkCenterOut(BaseModel):
    id: str
    plant_id: str
    name: str
    code: str
    capacity_per_hour: Decimal | None

    model_config = {"from_attributes": True}


class BOMComponentCreate(BaseModel):
    component_item_id: str
    # Required quantity of this component per 1 unit of the BOM's output item.
    quantity_per_unit: Decimal = Field(gt=0)


class BOMComponentOut(BaseModel):
    component_item_id: str
    component_sku: str
    quantity_per_unit: Decimal

    model_config = {"from_attributes": True}


class BOMCreate(BaseModel):
    output_item_id: str
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(default="1", max_length=20)
    components: list[BOMComponentCreate] = Field(min_length=1)


class BOMOut(BaseModel):
    id: str
    output_item_id: str
    name: str
    version: str
    is_active: bool
    components: list[BOMComponentOut]

    model_config = {"from_attributes": True}


class ProductionOrderCreate(BaseModel):
    plant_id: str
    bom_id: str
    work_center_id: str | None = None
    quantity_planned: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)


class ProductionOrderCompleteRequest(BaseModel):
    quantity: Decimal = Field(gt=0)


class ProductionOrderOut(BaseModel):
    id: str
    plant_id: str
    bom_id: str
    work_center_id: str | None
    quantity_planned: Decimal
    quantity_completed: Decimal
    status: ProductionOrderStatus
    reference: str | None

    model_config = {"from_attributes": True}
