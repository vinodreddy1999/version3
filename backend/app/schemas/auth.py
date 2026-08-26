from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ImpersonatorOut(ORMModel):
    id: str
    email: str
    full_name: str


class UserOut(ORMModel):
    id: str
    email: str
    full_name: str
    tenant_id: str
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
    impersonated_by: ImpersonatorOut | None = None


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterTenantRequest(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=200)
    tenant_slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=200)
    admin_full_name: str = Field(min_length=2, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    tenant_slug: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=200)


class MessageResponse(BaseModel):
    detail: str
