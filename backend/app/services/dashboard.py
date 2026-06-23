from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import DailyReportStatus, ProjectStatus
from app.models.client import Client
from app.models.daily_report import DailyReport
from app.models.material import Material
from app.models.project import Project
from app.models.project_material import ProjectMaterial
from app.models.project_worker import ProjectWorker
from app.models.worker import Worker
from app.schemas.dashboard import (
    DashboardResponse,
    KpiData,
    MaterialSummary,
    ProjectSummary,
    ReportSummary,
    WorkerSummary,
)


def get_dashboard(tenant_id: UUID, db: Session) -> DashboardResponse:
    projects = _project_summary(tenant_id, db)
    workers = _worker_summary(tenant_id, db)
    reports = _report_summary(tenant_id, db)
    materials = _material_summary(tenant_id, db)
    clients = _client_count(tenant_id, db)
    kpis = _calculate_kpis(tenant_id, db, projects)

    return DashboardResponse(
        projects=projects,
        workers=workers,
        daily_reports=reports,
        materials=materials,
        clients=clients,
        kpis=kpis,
    )


def _project_summary(tenant_id: UUID, db: Session) -> ProjectSummary:
    total = db.execute(
        select(func.count()).select_from(Project).where(
            Project.tenant_id == tenant_id
        )
    ).scalar() or 0

    rows = db.execute(
        select(Project.status, func.count()).where(
            Project.tenant_id == tenant_id
        ).group_by(Project.status)
    ).all()

    by_status = {row[0]: row[1] for row in rows}
    return ProjectSummary(
        total=total,
        planning=by_status.get(ProjectStatus.PLANNING, 0),
        in_progress=by_status.get(ProjectStatus.IN_PROGRESS, 0),
        completed=by_status.get(ProjectStatus.COMPLETED, 0),
        cancelled=by_status.get(ProjectStatus.CANCELLED, 0),
    )


def _worker_summary(tenant_id: UUID, db: Session) -> WorkerSummary:
    total = db.execute(
        select(func.count()).select_from(Worker).where(
            Worker.tenant_id == tenant_id
        )
    ).scalar() or 0

    active = db.execute(
        select(func.count()).select_from(Worker).where(
            Worker.tenant_id == tenant_id,
            Worker.is_active.is_(True),
        )
    ).scalar() or 0

    return WorkerSummary(total=total, active=active)


def _report_summary(tenant_id: UUID, db: Session) -> ReportSummary:
    today = date.today()
    today_count = db.execute(
        select(func.count()).select_from(DailyReport).where(
            DailyReport.tenant_id == tenant_id,
            DailyReport.date == today,
        )
    ).scalar() or 0

    pending = db.execute(
        select(func.count()).select_from(DailyReport).where(
            DailyReport.tenant_id == tenant_id,
            DailyReport.status == DailyReportStatus.SUBMITTED,
        )
    ).scalar() or 0

    return ReportSummary(today=today_count, pending_approval=pending)


def _material_summary(tenant_id: UUID, db: Session) -> MaterialSummary:
    low = db.execute(
        select(func.count()).select_from(Material).where(
            Material.tenant_id == tenant_id,
            Material.stock <= Material.min_stock,
        )
    ).scalar() or 0

    cats = db.execute(
        select(func.count(func.distinct(Material.category))).where(
            Material.tenant_id == tenant_id,
            Material.category.isnot(None),
        )
    ).scalar() or 0

    return MaterialSummary(low_stock=low, total_categories=cats)


def _client_count(tenant_id: UUID, db: Session) -> int:
    return (
        db.execute(
            select(func.count()).select_from(Client).where(
                Client.tenant_id == tenant_id
            )
        ).scalar()
        or 0
    )


def _calculate_kpis(
    tenant_id: UUID, db: Session, projects: ProjectSummary
) -> KpiData:
    total_projects = projects.total
    completion_rate = (
        round(projects.completed / total_projects, 4) if total_projects else 0.0
    )

    budget_result = db.execute(
        select(
            func.sum(Project.budget),
            func.sum(ProjectMaterial.total_price),
        )
        .select_from(Project)
        .outerjoin(
            ProjectMaterial,
            ProjectMaterial.project_id == Project.id,
        )
        .where(Project.tenant_id == tenant_id)
    ).first()
    total_budget = budget_result[0] or 0
    total_spent = budget_result[1] or 0
    budget_util = (
        round(total_spent / total_budget, 4) if total_budget else 0.0
    )

    today = date.today()
    report_count = db.execute(
        select(func.count()).select_from(DailyReport).where(
            DailyReport.tenant_id == tenant_id,
            DailyReport.date == today,
        )
    ).scalar() or 0

    active_workers = db.execute(
        select(func.count()).select_from(Worker).where(
            Worker.tenant_id == tenant_id,
            Worker.is_active.is_(True),
        )
    ).scalar() or 1

    avg_hours = db.execute(
        select(func.avg(DailyReport.hours_worked)).where(
            DailyReport.tenant_id == tenant_id,
            DailyReport.date == today,
        )
    ).scalar() or 0.0

    assignments = db.execute(
        select(func.count()).select_from(ProjectWorker).where(
            ProjectWorker.tenant_id == tenant_id,
            ProjectWorker.is_active.is_(True),
        )
    ).scalar() or 0

    return KpiData(
        project_completion_rate=completion_rate,
        budget_utilization=budget_util,
        report_submission_rate=round(report_count / active_workers, 4),
        avg_hours_per_worker=round(float(avg_hours), 2),
        total_material_cost=round(float(total_spent), 2),
        active_assignments=assignments,
    )
