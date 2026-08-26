from pydantic import BaseModel, Field

from app.schemas.base import ORMModel


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)


class CompanyOut(ORMModel):
    id: str
    name: str
    code: str
    is_active: bool


class PlantCreate(BaseModel):
    company_id: str
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    address: str | None = None


class PlantOut(ORMModel):
    id: str
    company_id: str
    name: str
    code: str
    address: str | None
    is_active: bool
