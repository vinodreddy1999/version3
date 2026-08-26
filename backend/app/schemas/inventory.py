from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.inventory import ItemType, MovementType
from app.schemas.base import ORMModel


class ItemCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    item_type: ItemType
    uom: str = Field(default="EA", max_length=20)
    reorder_point: Decimal = Decimal("0")


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    uom: str | None = Field(default=None, max_length=20)
    reorder_point: Decimal | None = None
    is_active: bool | None = None


class ItemOut(ORMModel):
    id: str
    sku: str
    name: str
    description: str | None
    item_type: ItemType
    uom: str
    reorder_point: Decimal
    is_active: bool


class StockBalanceOut(ORMModel):
    id: str
    plant_id: str
    item_id: str
    item_sku: str
    item_name: str
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal


class StockMovementCreate(BaseModel):
    plant_id: str
    item_id: str
    movement_type: MovementType
    # Positive magnitude for receipt/issue/transfer_in/transfer_out (direction
    # comes from movement_type); for adjustment, any nonzero signed delta.
    quantity: Decimal
    reference: str | None = Field(default=None, max_length=200)
    notes: str | None = None


class StockMovementOut(ORMModel):
    id: str
    plant_id: str
    item_id: str
    movement_type: MovementType
    quantity: Decimal
    reference: str | None
    notes: str | None
    created_by_user_id: str
