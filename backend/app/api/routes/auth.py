import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.audit import record_audit
from app.core.config import settings
from app.core.email import EmailBackend, get_email_backend
from app.core.permissions import PERMISSION_CODES
from app.core.rate_limit import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.core.seed import seed_permissions
from app.models.base import utcnow
from app.models.password_reset import PasswordResetToken
from app.models.tenant import Tenant
from app.models.user import Permission, Role, User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterTenantRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
)

_PASSWORD_RESET_TOKEN_TTL = timedelta(hours=1)
_GENERIC_FORGOT_PASSWORD_RESPONSE = MessageResponse(
    detail="If an account with that email exists, a password reset link has been sent."
)

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


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("5/hour")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db_session),
    email_backend: EmailBackend = Depends(get_email_backend),
) -> MessageResponse:
    # Always return the same generic response regardless of whether the
    # tenant/email/account exists, so this endpoint can't be used to
    # enumerate valid accounts.
    tenant = db.query(Tenant).filter(Tenant.slug == payload.tenant_slug, Tenant.is_active.is_(True)).first()
    if tenant is None:
        return _GENERIC_FORGOT_PASSWORD_RESPONSE

    user = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.email == payload.email, User.is_active.is_(True))
        .first()
    )
    if user is None:
        return _GENERIC_FORGOT_PASSWORD_RESPONSE

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=utcnow() + _PASSWORD_RESET_TOKEN_TTL,
        )
    )

    reset_link = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
    email_backend.send(
        to=user.email,
        subject="Reset your Metam ERP password",
        body=f"Someone requested a password reset for your account.\n\n"
        f"Reset your password: {reset_link}\n\n"
        f"This link expires in 1 hour. If you didn't request this, you can ignore this email.",
    )

    record_audit(
        db,
        tenant_id=tenant.id,
        actor=user,
        action="user.password_reset_requested",
        entity_type="user",
        entity_id=user.id,
        summary=f"{user.email} requested a password reset",
    )
    db.commit()
    return _GENERIC_FORGOT_PASSWORD_RESPONSE


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/hour")
def reset_password(
    request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db_session)
) -> MessageResponse:
    invalid_token = HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid or expired reset link")

    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if reset_token is None or reset_token.used_at is not None:
        raise invalid_token
    # SQLite drops timezone info on round-trip (unlike Postgres), so
    # DateTime(timezone=True) columns come back naive there — normalize
    # both sides to naive UTC before comparing rather than relying on
    # tzinfo being present.
    expires_at = reset_token.expires_at.replace(tzinfo=None)
    if expires_at < utcnow().replace(tzinfo=None):
        raise invalid_token

    user = db.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        raise invalid_token

    user.hashed_password = hash_password(payload.new_password)
    reset_token.used_at = utcnow()
    record_audit(
        db,
        tenant_id=user.tenant_id,
        actor=user,
        action="user.password_reset",
        entity_type="user",
        entity_id=user.id,
        summary=f"{user.email} reset their password",
    )
    db.commit()
    return MessageResponse(detail="Password updated. You can now sign in.")


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
