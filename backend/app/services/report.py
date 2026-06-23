from uuid import UUID

from app.repositories.report import ReportRepository
from app.schemas.report import ReportCreate
from app.services.base import BaseService
from app.workers.tasks.reports import generate_report


class ReportService(BaseService):
    def __init__(self, repo: ReportRepository):
        super().__init__(repo)

    def create(self, data: ReportCreate, tenant_id: UUID, user_id: UUID) -> ...:
        report = self.repo.create(
            {
                "project_id": data.project_id,
                "type": data.type,
                "name": data.name,
                "parameters": data.parameters or {},
                "generated_by": user_id,
            },
            tenant_id=tenant_id,
        )
        generate_report.delay(str(report.id))
        return report
