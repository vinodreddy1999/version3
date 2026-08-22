from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.quality import DefectSeverity, DefectStatus, InspectionResult


class DefectCreate(BaseModel):
    defect_type: str = Field(min_length=1, max_length=100)
    severity: DefectSeverity
    quantity: Decimal = Field(gt=0)
    description: str | None = None


class DefectOut(BaseModel):
    id: str
    defect_type: str
    severity: DefectSeverity
    quantity: Decimal
    description: str | None
    status: DefectStatus

    model_config = {"from_attributes": True}


class InspectionCreate(BaseModel):
    plant_id: str
    item_id: str
    inspected_quantity: Decimal = Field(gt=0)
    reference: str | None = Field(default=None, max_length=200)
    notes: str | None = None
    defects: list[DefectCreate] = Field(default_factory=list)


class InspectionOut(BaseModel):
    id: str
    plant_id: str
    item_id: str
    reference: str | None
    inspected_quantity: Decimal
    result: InspectionResult
    notes: str | None
    defects: list[DefectOut]

    model_config = {"from_attributes": True}
