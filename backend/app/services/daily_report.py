from uuid import UUID

from app.core.constants import DailyReportStatus
from app.core.exceptions import ConflictError, ValidationError
from app.repositories.daily_report import DailyReportRepository
from app.schemas.daily_report import DailyReportCreate, DailyReportStatusUpdate
from app.services.base import BaseService


class DailyReportService(BaseService):
    def __init__(self, repo: DailyReportRepository):
        super().__init__(repo)

    def create(self, data: DailyReportCreate, tenant_id: UUID) -> ...:
        existing = self.repo.get_by_worker_date(
            data.worker_id, data.date, tenant_id
        )
        if existing:
            raise ConflictError(
                "A report already exists for this worker on this date"
            )
        return self.repo.create(data, tenant_id=tenant_id)

    def update_status(
        self,
        report_id: UUID,
        data: DailyReportStatusUpdate,
        tenant_id: UUID,
        user_id: UUID,
    ) -> ...:
        report = self.repo.get(report_id, tenant_id)
        self._validate_transition(report.status, data.status)
        return self.repo.update(
            report_id,
            {
                "status": data.status,
                "approved_by": user_id,
                "notes": data.notes,
            },
            tenant_id=tenant_id,
        )

    @staticmethod
    def _validate_transition(current: DailyReportStatus, target: DailyReportStatus) -> None:
        valid = {
            DailyReportStatus.DRAFT: {DailyReportStatus.SUBMITTED},
            DailyReportStatus.SUBMITTED: {
                DailyReportStatus.APPROVED,
                DailyReportStatus.REJECTED,
            },
            DailyReportStatus.APPROVED: set(),
            DailyReportStatus.REJECTED: set(),
        }
        allowed = valid.get(current, set())
        if target not in allowed:
            raise ValidationError(
                f"Cannot transition from {current} to {target}"
            )
