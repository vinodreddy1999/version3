from collections.abc import Generator
from typing import TypeVar

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

T = TypeVar("T")


class PaginationParams:
    """limit/offset pagination. Default limit is generous enough that
    reference-data dropdowns (items, suppliers, work centers, ...) still see
    everything for realistically-sized tenants, while still capping the
    worst case for lists that can grow without bound (movements, orders)."""

    def __init__(self, limit: int = Query(200, ge=1, le=500), offset: int = Query(0, ge=0)):
        self.limit = limit
        self.offset = offset


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    if payload.get("type") != "access":
        raise credentials_error

    user_id = payload.get("sub")
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise credentials_error
    # Transient, unmapped attribute — not persisted, just threads the
    # impersonation claim from the token through to route handlers (namely
    # /api/auth/me) without a second dependency every route would need.
    user.impersonated_by_id = payload.get("impersonated_by")
    return user


def get_owned(db: Session, model: type[T], entity_id: str, user: User, label: str) -> T:
    """Fetch a row by id and 404 unless it belongs to the caller's tenant.
    Only for models with a direct `tenant_id` column — ones scoped via a
    relationship (e.g. Plant -> Company, Bin -> Zone -> Warehouse) or that
    need eager-loaded relations keep their own `_get_owned_*` helper."""
    obj = db.get(model, entity_id)
    if obj is None or obj.tenant_id != user.tenant_id:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


def require_permissions(*required_codes: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user
        granted = {perm.code for role in user.roles for perm in role.permissions}
        if not set(required_codes).issubset(granted):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency
