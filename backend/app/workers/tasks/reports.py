"""Report generation tasks — PDF builds triggered by ReportService.create().

Uses shared DB session and sends notification on completion.
"""

from datetime import date
from uuid import UUID

from app.core.constants import ReportStatus
from app.models.daily_report import DailyReport
from app.models.project import Project
from app.models.project_material import ProjectMaterial
from app.models.report import Report
from app.models.worker import Worker
from app.utils.pdf_generator import generate_report_pdf
from app.workers.celery_app import celery_app
from app.workers.db import get_db


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=120,
    acks_late=True,
)
def generate_report(self, report_id: str) -> None:
    with get_db() as db:
        report: Report | None = (
            db.query(Report)
            .filter(Report.id == UUID(report_id))
            .first()
        )
        if not report:
            return

        report.status = ReportStatus.PROCESSING
        db.flush()

        try:
            data = _build_report_data(report, db)
            filename = f"{report.type}_{report.id.hex[:8]}.pdf"
            file_path = generate_report_pdf(report.name, data, filename)

            report.data = data
            report.file_path = file_path
            report.status = ReportStatus.COMPLETED

        except Exception as exc:
            report.status = ReportStatus.FAILED
            report.error = str(exc)
            db.flush()
            raise self.retry(exc=exc)

    if report and report.status == ReportStatus.COMPLETED:
        _notify_report_ready.delay(str(report.id), str(report.generated_by))


@celery_app.task(acks_late=True)
def _notify_report_ready(report_id: str, user_id: str) -> None:
    from app.workers.tasks.notifications import send_notification

    send_notification(
        user_id=UUID(user_id),
        title="Report Ready",
        body=f"Report ({report_id[:8]}) has been generated and is available.",
        notification_type="report_ready",
    )


def _build_report_data(report: Report, db) -> dict:
    base: dict = {
        "report": {
            "name": report.name,
            "type": report.type,
            "date": date.today().isoformat(),
        }
    }

    if report.project_id:
        project = (
            db.query(Project)
            .filter(
                Project.id == report.project_id,
                Project.tenant_id == report.tenant_id,
            )
            .first()
        )
        if project:
            base["project"] = {
                "name": project.name,
                "code": project.code,
                "status": project.status,
                "budget": float(project.budget or 0),
            }

            materials = (
                db.query(ProjectMaterial)
                .filter(
                    ProjectMaterial.project_id == project.id,
                    ProjectMaterial.tenant_id == report.tenant_id,
                )
                .all()
            )
            total_material_cost = sum(
                float(m.total_price) for m in materials
            )
            base["materials"] = {
                "total_cost": total_material_cost,
                "items_count": len(materials),
            }

            workers_on_project = (
                db.query(Worker)
                .join(
                    DailyReport,
                    DailyReport.worker_id == Worker.id,
                )
                .filter(
                    DailyReport.project_id == project.id,
                    DailyReport.tenant_id == report.tenant_id,
                )
                .distinct()
                .count()
            )
            base["workers"] = {"active_on_project": workers_on_project}

    if report.type == "monthly":
        all_reports = (
            db.query(DailyReport)
            .filter(DailyReport.tenant_id == report.tenant_id)
            .all()
        )
        total_hours = sum(float(r.hours_worked) for r in all_reports)
        base["monthly_summary"] = {
            "total_reports": len(all_reports),
            "total_hours": round(total_hours, 1),
        }

    return base
