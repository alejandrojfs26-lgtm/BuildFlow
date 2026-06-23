
from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.core.constants import ROLE_PERMISSIONS, Permission
from app.models.user import User


def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def require_permissions(*permissions: Permission):
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        for perm in permissions:
            if not has_permission(current_user, perm):
                from app.core.exceptions import ForbiddenError

                raise ForbiddenError(
                    f"Missing permission: {perm.value}"
                )
        return current_user

    return _check
