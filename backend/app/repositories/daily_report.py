from datetime import date
from uuid import UUID

from sqlalchemy import select

from app.models.daily_report import DailyReport
from app.repositories.base import BaseRepository


class DailyReportRepository(BaseRepository[DailyReport]):
    def __init__(self, db):
        super().__init__(DailyReport, db)

    def get_by_worker_date(
        self, worker_id: UUID, report_date: date, tenant_id: UUID
    ) -> DailyReport | None:
        return self.db.execute(
            select(DailyReport).where(
                DailyReport.worker_id == worker_id,
                DailyReport.date == report_date,
                DailyReport.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
