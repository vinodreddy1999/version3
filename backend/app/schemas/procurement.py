from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.models.procurement import PurchaseOrderStatus


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=50)


class SupplierOut(BaseModel):
    id: str
    name: str
    code: str
    contact_email: str | None
    contact_phone: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PurchaseOrderLineCreate(BaseModel):
    item_id: str
    quantity_ordered: Decimal = Field(gt=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)


class PurchaseOrderLineOut(BaseModel):
    id: str
    item_id: str
    item_sku: str
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal

    model_config = {"from_attributes": True}


class PurchaseOrderCreate(BaseModel):
    plant_id: str
    supplier_id: str
    reference: str | None = Field(default=None, max_length=200)
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderOut(BaseModel):
    id: str
    plant_id: str
    supplier_id: str
    reference: str | None
    status: PurchaseOrderStatus
    lines: list[PurchaseOrderLineOut]

    model_config = {"from_attributes": True}


class ReceiveLineRequest(BaseModel):
    line_id: str
    quantity: Decimal = Field(gt=0)
