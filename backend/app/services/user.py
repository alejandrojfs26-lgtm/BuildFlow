from uuid import UUID

from app.auth.password import hash_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.base import BaseService


class UserService(BaseService):
    def __init__(self, repo: UserRepository):
        super().__init__(repo)

    def create(self, data: UserCreate, tenant_id: UUID) -> UserResponse:
        self.repo.assert_unique("email", data.email)
        user = self.repo.create(
            {
                "email": data.email,
                "password_hash": hash_password(data.password),
                "full_name": data.full_name,
                "role": data.role,
            },
            tenant_id=tenant_id,
        )
        return UserResponse.model_validate(user)
