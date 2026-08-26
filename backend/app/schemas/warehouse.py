from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.warehouse import TaskStatus, ZoneType
from app.schemas.base import ORMModel


class WarehouseCreate(BaseModel):
    plant_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)


class WarehouseOut(ORMModel):
    id: str
    plant_id: str
    name: str
    code: str


class ZoneCreate(BaseModel):
    warehouse_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    zone_type: ZoneType


class ZoneOut(ORMModel):
    id: str
    warehouse_id: str
    name: str
    code: str
    zone_type: ZoneType


class BinCreate(BaseModel):
    zone_id: str
    code: str = Field(min_length=1, max_length=50)


class BinOut(ORMModel):
    id: str
    zone_id: str
    code: str


class BinStockOut(ORMModel):
    bin_id: str
    bin_code: str
    item_id: str
    item_sku: str
    quantity: Decimal


class PutawayTaskCreate(BaseModel):
    plant_id: str
    item_id: str
    destination_bin_id: str
    quantity: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)


class PutawayTaskOut(ORMModel):
    id: str
    plant_id: str
    item_id: str
    destination_bin_id: str
    quantity: Decimal
    reference: str | None
    status: TaskStatus


class PickTaskCreate(BaseModel):
    plant_id: str
    item_id: str
    source_bin_id: str
    quantity: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)


class PickTaskOut(ORMModel):
    id: str
    plant_id: str
    item_id: str
    source_bin_id: str
    quantity: Decimal
    reference: str | None
    status: TaskStatus
