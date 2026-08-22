from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.warehouse import TaskStatus, ZoneType


class WarehouseCreate(BaseModel):
    plant_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)


class WarehouseOut(BaseModel):
    id: str
    plant_id: str
    name: str
    code: str

    model_config = {"from_attributes": True}


class ZoneCreate(BaseModel):
    warehouse_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    zone_type: ZoneType


class ZoneOut(BaseModel):
    id: str
    warehouse_id: str
    name: str
    code: str
    zone_type: ZoneType

    model_config = {"from_attributes": True}


class BinCreate(BaseModel):
    zone_id: str
    code: str = Field(min_length=1, max_length=50)


class BinOut(BaseModel):
    id: str
    zone_id: str
    code: str

    model_config = {"from_attributes": True}


class BinStockOut(BaseModel):
    bin_id: str
    bin_code: str
    item_id: str
    item_sku: str
    quantity: Decimal

    model_config = {"from_attributes": True}


class PutawayTaskCreate(BaseModel):
    plant_id: str
    item_id: str
    destination_bin_id: str
    quantity: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)


class PutawayTaskOut(BaseModel):
    id: str
    plant_id: str
    item_id: str
    destination_bin_id: str
    quantity: Decimal
    reference: str | None
    status: TaskStatus

    model_config = {"from_attributes": True}


class PickTaskCreate(BaseModel):
    plant_id: str
    item_id: str
    source_bin_id: str
    quantity: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)


class PickTaskOut(BaseModel):
    id: str
    plant_id: str
    item_id: str
    source_bin_id: str
    quantity: Decimal
    reference: str | None
    status: TaskStatus

    model_config = {"from_attributes": True}
