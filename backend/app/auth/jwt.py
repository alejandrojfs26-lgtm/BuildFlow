from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "type": TokenType.ACCESS,
        "exp": _now() + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: UUID) -> str:
    import uuid as _uuid

    payload = {
        "sub": str(user_id),
        "type": TokenType.REFRESH,
        "jti": _uuid.uuid4().hex,
        "exp": _now() + timedelta(days=settings.refresh_token_expire_days),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        return {}
