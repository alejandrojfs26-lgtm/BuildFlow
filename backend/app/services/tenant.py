from uuid import UUID

from app.repositories.tenant import TenantRepository
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.base import BaseService


class TenantService(BaseService):
    def __init__(self, repo: TenantRepository):
        super().__init__(repo)

    def create(self, data: TenantCreate) -> ...:
        self.repo.assert_unique("slug", data.slug)
        if data.tax_id:
            self.repo.assert_unique("tax_id", data.tax_id)
        return self.repo.create(data)

    def update(self, entity_id: UUID, data: TenantUpdate) -> ...:
        return self.repo.update(entity_id, data)
