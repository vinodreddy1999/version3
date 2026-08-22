from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.audit import record_audit
from app.core.permissions import PERMISSION_CODES
from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.core.seed import seed_permissions
from app.models.tenant import Tenant
from app.models.user import Permission, Role, User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterTenantRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenResponse:
    role_names = [role.name for role in user.roles]
    return TokenResponse(
        access_token=create_access_token(user.id, tenant_id=user.tenant_id, roles=role_names),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/register-tenant", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register_tenant(
    request: Request, payload: RegisterTenantRequest, db: Session = Depends(get_db_session)
) -> TokenResponse:
    if db.query(Tenant).filter(Tenant.slug == payload.tenant_slug).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already in use")

    seed_permissions(db)

    tenant = Tenant(name=payload.tenant_name, slug=payload.tenant_slug)
    db.add(tenant)
    db.flush()

    admin_role = Role(tenant_id=tenant.id, name="Admin", is_system=True)
    admin_role.permissions = db.query(Permission).all()
    db.add(admin_role)
    db.flush()

    admin_user = User(
        tenant_id=tenant.id,
        email=payload.admin_email,
        hashed_password=hash_password(payload.admin_password),
        full_name=payload.admin_full_name,
        is_superuser=True,
    )
    admin_user.roles.append(admin_role)
    db.add(admin_user)
    db.flush()

    record_audit(
        db,
        tenant_id=tenant.id,
        actor=admin_user,
        action="tenant.registered",
        entity_type="tenant",
        entity_id=tenant.id,
        summary=f"Organization '{tenant.name}' registered by {admin_user.email}",
    )
    db.commit()
    db.refresh(admin_user)

    return _issue_tokens(admin_user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db_session)) -> TokenResponse:
    tenant = db.query(Tenant).filter(Tenant.slug == payload.tenant_slug, Tenant.is_active.is_(True)).first()
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email, password, or tenant"
    )
    if tenant is None:
        raise invalid_credentials

    user = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.email == payload.email, User.is_active.is_(True))
        .first()
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    record_audit(
        db,
        tenant_id=tenant.id,
        actor=user,
        action="user.login",
        entity_type="user",
        entity_id=user.id,
        summary=f"{user.email} logged in",
    )
    db.commit()

    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db_session)) -> TokenResponse:
    invalid_token = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise invalid_token from exc

    if decoded.get("type") != "refresh":
        raise invalid_token

    user = db.get(User, decoded.get("sub"))
    if user is None or not user.is_active:
        raise invalid_token

    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    permissions = (
        sorted(PERMISSION_CODES)
        if user.is_superuser
        else sorted({perm.code for role in user.roles for perm in role.permissions})
    )
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=user.tenant_id,
        is_superuser=user.is_superuser,
        roles=[role.name for role in user.roles],
        permissions=permissions,
    )
