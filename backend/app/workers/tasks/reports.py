from datetime import date
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.constants import ReportStatus
from app.models.daily_report import DailyReport
from app.models.project import Project
from app.models.project_material import ProjectMaterial
from app.models.report import Report
from app.models.worker import Worker
from app.utils.pdf_generator import generate_report_pdf
from app.workers.celery_app import celery_app

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@celery_app.task(bind=True, max_retries=2)
def generate_report(self, report_id: str) -> None:
    db: Session = SessionLocal()
    try:
        report = db.query(Report).filter(Report.id == UUID(report_id)).first()
        if not report:
            return

        report.status = ReportStatus.PROCESSING
        db.flush()

        data = _build_report_data(report, db)

        filename = f"{report.type}_{report.id.hex[:8]}.pdf"
        file_path = generate_report_pdf(report.name, data, filename)

        report.data = data
        report.file_path = file_path
        report.status = ReportStatus.COMPLETED
        db.commit()

    except Exception as exc:
        db.rollback()
        db.query(Report).filter(Report.id == UUID(report_id)).update(
            {"status": ReportStatus.FAILED, "error": str(exc)}
        )
        db.commit()
        raise self.retry(exc=exc)

    finally:
        db.close()


def _build_report_data(report: Report, db: Session) -> dict:
    base = {
        "report": {
            "name": report.name,
            "type": report.type,
            "date": date.today().isoformat(),
        }
    }

    if report.project_id:
        project = db.query(Project).filter(
            Project.id == report.project_id,
            Project.tenant_id == report.tenant_id,
        ).first()
        if project:
            base["project"] = {
                "name": project.name,
                "code": project.code,
                "status": project.status,
                "budget": float(project.budget or 0),
            }

            materials = db.query(ProjectMaterial).filter(
                ProjectMaterial.project_id == project.id,
                ProjectMaterial.tenant_id == report.tenant_id,
            ).all()
            total_material_cost = sum(m.total_price for m in materials)
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
        reports = db.query(DailyReport).filter(
            DailyReport.tenant_id == report.tenant_id,
        ).all()
        total_hours = sum(r.hours_worked for r in reports)
        base["monthly_summary"] = {
            "total_reports": len(reports),
            "total_hours": round(total_hours, 1),
        }

    return base
