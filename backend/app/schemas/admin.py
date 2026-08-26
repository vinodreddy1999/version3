from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import ORMModel


class PermissionOut(ORMModel):
    code: str
    description: str | None


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    permission_codes: list[str] | None = None


class RoleOut(ORMModel):
    id: str
    name: str
    is_system: bool
    permission_codes: list[str]


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    role_ids: list[str] = Field(default_factory=list)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None
    is_superuser: bool | None = None
    role_ids: list[str] | None = None


class UserAdminOut(ORMModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role_ids: list[str]
    role_names: list[str]


class AuditLogOut(ORMModel):
    id: str
    action: str
    entity_type: str
    entity_id: str | None
    summary: str
    actor_email: str | None
    created_at: datetime
