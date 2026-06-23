from uuid import UUID

from app.core.exceptions import ConflictError, ValidationError
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate
from app.services.base import BaseService


class ProjectService(BaseService):
    def __init__(self, repo: ProjectRepository):
        super().__init__(repo)

    def create(self, data: ProjectCreate, tenant_id: UUID) -> ...:
        existing = self.repo.get_by_code(data.code, tenant_id)
        if existing:
            raise ConflictError(f"Project with code '{data.code}' already exists")

        if data.end_date and data.start_date and data.end_date < data.start_date:
            raise ValidationError("end_date must be after start_date")

        return self.repo.create(data, tenant_id=tenant_id)
