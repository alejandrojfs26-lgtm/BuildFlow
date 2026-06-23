from uuid import UUID

from app.repositories.export import ExportRepository
from app.schemas.export import ExportCreate
from app.services.base import BaseService
from app.workers.tasks.exports import run_export


class ExportService(BaseService):
    def __init__(self, repo: ExportRepository):
        super().__init__(repo)

    def create(self, data: ExportCreate, tenant_id: UUID, user_id: UUID) -> ...:
        export = self.repo.create(
            {
                "entity_type": data.entity_type,
                "format": data.format,
                "created_by": user_id,
            },
            tenant_id=tenant_id,
        )
        run_export.delay(str(export.id))
        return export
