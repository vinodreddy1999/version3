from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt's underlying algorithm only uses the first 72 bytes of the input;
# passing longer input raises in bcrypt>=4, so cap explicitly rather than
# letting arbitrarily long passwords error out at hash/verify time.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(truncated, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    truncated = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    try:
        return bcrypt.checkpw(truncated, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, expires_delta: timedelta, extra_claims: dict[str, Any], token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
        **extra_claims,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str,
    tenant_id: str | None = None,
    roles: list[str] | None = None,
    impersonated_by: str | None = None,
) -> str:
    extra = {"tenant_id": tenant_id, "roles": roles or []}
    if impersonated_by:
        extra["impersonated_by"] = impersonated_by
    return _create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        extra,
        "access",
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, timedelta(minutes=settings.refresh_token_expire_minutes), {}, "refresh")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
