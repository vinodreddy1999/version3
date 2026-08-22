from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.sales import SalesOrderStatus


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=50)


class CustomerOut(BaseModel):
    id: str
    name: str
    code: str
    contact_email: str | None
    contact_phone: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class SalesOrderLineCreate(BaseModel):
    item_id: str
    quantity_ordered: Decimal = Field(gt=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)


class SalesOrderLineOut(BaseModel):
    id: str
    item_id: str
    item_sku: str
    quantity_ordered: Decimal
    quantity_shipped: Decimal
    unit_price: Decimal

    model_config = {"from_attributes": True}


class SalesOrderCreate(BaseModel):
    plant_id: str
    customer_id: str
    reference: str | None = Field(default=None, max_length=200)
    lines: list[SalesOrderLineCreate] = Field(min_length=1)


class SalesOrderOut(BaseModel):
    id: str
    plant_id: str
    customer_id: str
    reference: str | None
    status: SalesOrderStatus
    lines: list[SalesOrderLineOut]

    model_config = {"from_attributes": True}


class ShipLineRequest(BaseModel):
    line_id: str
    quantity: Decimal = Field(gt=0)
