from uuid import UUID

from app.core.exceptions import ConflictError
from app.repositories.assignment import AssignmentRepository
from app.schemas.assignment import AssignmentCreate
from app.services.base import BaseService


class AssignmentService(BaseService):
    def __init__(self, repo: AssignmentRepository):
        super().__init__(repo)

    def create(self, data: AssignmentCreate, tenant_id: UUID) -> ...:
        existing = self.repo.get_by_project_and_worker(
            data.project_id, data.worker_id, tenant_id
        )
        if existing:
            raise ConflictError("Worker is already assigned to this project")
        return self.repo.create(data, tenant_id=tenant_id)
