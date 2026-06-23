from uuid import UUID

from sqlalchemy import select

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, db):
        super().__init__(Tenant, db)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return self.db.execute(
            select(Tenant).where(Tenant.slug == slug)
        ).scalar_one_or_none()

    def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        return self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        ).scalar_one_or_none()
