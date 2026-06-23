from typing import Any, Generic, TypeVar
from uuid import UUID

from app.repositories.base import BaseRepository

ModelT = TypeVar("ModelT")


class BaseService(Generic[ModelT]):
    def __init__(self, repo: BaseRepository[ModelT]):
        self.repo = repo

    def get(self, entity_id: UUID, tenant_id: UUID | None = None) -> ModelT:
        return self.repo.get(entity_id, tenant_id)

    def list(
        self,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str | None = None,
        descending: bool = False,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        return self.repo.list(
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            order_by=order_by,
            descending=descending,
            filters=filters,
        )

    def create(self, data: Any, tenant_id: UUID | None = None) -> ModelT:
        return self.repo.create(data, tenant_id)

    def update(
        self, entity_id: UUID, data: Any, tenant_id: UUID | None = None
    ) -> ModelT:
        return self.repo.update(entity_id, data, tenant_id)

    def delete(self, entity_id: UUID, tenant_id: UUID | None = None) -> None:
        self.repo.delete(entity_id, tenant_id)
