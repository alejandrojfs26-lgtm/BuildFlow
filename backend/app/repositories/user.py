from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

    def list_by_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[User], int]:
        return self.list(tenant_id=tenant_id, skip=skip, limit=limit)
