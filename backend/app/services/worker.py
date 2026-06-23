from uuid import UUID

from app.core.exceptions import ConflictError
from app.repositories.worker import WorkerRepository
from app.schemas.worker import WorkerCreate
from app.services.base import BaseService


class WorkerService(BaseService):
    def __init__(self, repo: WorkerRepository):
        super().__init__(repo)

    def create(self, data: WorkerCreate, tenant_id: UUID) -> ...:
        existing = self.repo.get_by_dni(data.dni, tenant_id)
        if existing:
            raise ConflictError(
                f"Worker with DNI '{data.dni}' already exists in this tenant"
            )
        return self.repo.create(data, tenant_id=tenant_id)
