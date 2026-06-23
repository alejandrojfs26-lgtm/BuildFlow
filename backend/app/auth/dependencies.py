from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.auth.jwt import TokenExpiredError, TokenInvalidError, TokenType, decode_token
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository


async def get_token_from_header(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header")
    return authorization.removeprefix("Bearer ")


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except TokenExpiredError:
        raise UnauthorizedError("Token expired")
    except TokenInvalidError:
        raise UnauthorizedError("Invalid token")

    user_id = payload.get("sub")
    token_type = payload.get("type")

    if not user_id or token_type != TokenType.ACCESS:
        raise UnauthorizedError("Invalid or expired token")

    repo = UserRepository(db)
    user = repo.get_by_id(UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def get_current_tenant_id(
    current_user: User = Depends(get_current_user),
) -> UUID:
    return current_user.tenant_id


async def get_current_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "super_admin":
        raise ForbiddenError("Super admin access required")
    return current_user
