from uuid import UUID

from app.core.exceptions import ValidationError
from app.repositories.material import MaterialRepository
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.services.base import BaseService


class MaterialService(BaseService):
    def __init__(self, repo: MaterialRepository):
        super().__init__(repo)

    def create(self, data: MaterialCreate, tenant_id: UUID) -> ...:
        if data.stock is not None and data.stock < 0:
            raise ValidationError("stock cannot be negative")
        if data.min_stock is not None and data.min_stock < 0:
            raise ValidationError("min_stock cannot be negative")
        return self.repo.create(data, tenant_id=tenant_id)

    def update(self, entity_id: UUID, data: MaterialUpdate, tenant_id: UUID) -> ...:
        return self.repo.update(entity_id, data, tenant_id=tenant_id)
