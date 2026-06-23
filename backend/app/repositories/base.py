import time
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, UnaryExpression, desc, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.metrics import db_query_duration_seconds, db_query_errors_total
from app.db.base_class import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], db: Session):
        self.model = model
        self.db = db

    def _scope_by_tenant(self, query: Select, tenant_id: UUID | None) -> Select:
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        return query

    def _timed_execute(self, operation: str, stmt, *args, **kwargs):
        start = time.monotonic()
        try:
            result = self.db.execute(stmt, *args, **kwargs)
            return result
        except Exception:
            db_query_errors_total.labels(operation=operation).inc()
            raise
        finally:
            duration = time.monotonic() - start
            db_query_duration_seconds.labels(operation=operation).observe(duration)

    def get(self, entity_id: UUID, tenant_id: UUID | None = None) -> ModelT:
        query = select(self.model).where(self.model.id == entity_id)
        query = self._scope_by_tenant(query, tenant_id)
        result = self._timed_execute("get", query).scalar_one_or_none()
        if not result:
            raise NotFoundError(f"{self.model.__name__} {entity_id} not found")
        return result

    def list(
        self,
        tenant_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str | None = None,
        descending: bool = False,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelT], int]:
        query = select(self.model)
        query = self._scope_by_tenant(query, tenant_id)

        if filters:
            for field, value in filters.items():
                col = getattr(self.model, field, None)
                if col is not None:
                    query = query.where(col == value)

        count_query = select(func.count()).select_from(query.subquery())
        total = self._timed_execute("count", count_query).scalar() or 0

        if order_by:
            col = getattr(self.model, order_by, None)
            if col is not None:
                order: UnaryExpression = (
                    desc(col) if descending else col.asc()
                )
                query = query.order_by(order)

        query = query.offset(skip).limit(limit)
        results = list(self._timed_execute("list", query).scalars().all())
        return results, total

    def create(self, data: Any, tenant_id: UUID | None = None) -> ModelT:
        kwargs = data.model_dump() if hasattr(data, "model_dump") else data
        if tenant_id is not None and hasattr(self.model, "tenant_id"):
            kwargs["tenant_id"] = tenant_id
        entity = self.model(**kwargs)
        self.db.add(entity)
        self._timed_execute("create", self.db.flush())
        return entity

    def update(
        self, entity_id: UUID, data: Any, tenant_id: UUID | None = None
    ) -> ModelT:
        entity = self.get(entity_id, tenant_id)
        update_data = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else data
        )
        for field, value in update_data.items():
            setattr(entity, field, value)
        self._timed_execute("update", self.db.flush())
        return entity

    def delete(self, entity_id: UUID, tenant_id: UUID | None = None) -> None:
        entity = self.get(entity_id, tenant_id)
        self.db.delete(entity)
        self._timed_execute("delete", self.db.flush())

    def exists(
        self, field: str, value: Any, tenant_id: UUID | None = None
    ) -> bool:
        col = getattr(self.model, field, None)
        if col is None:
            return False
        query = select(self.model).where(col == value)
        query = self._scope_by_tenant(query, tenant_id)
        return self._timed_execute("exists", query).scalar_one_or_none() is not None

    def assert_unique(
        self, field: str, value: Any, tenant_id: UUID | None = None
    ) -> None:
        if self.exists(field, value, tenant_id):
            entity_name = self.model.__name__
            raise ConflictError(f"{entity_name} with {field} '{value}' already exists")
