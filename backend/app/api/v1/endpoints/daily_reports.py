from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.daily_report import DailyReportRepository
from app.schemas.common import Message
from app.schemas.daily_report import (
    DailyReportCreate,
    DailyReportResponse,
    DailyReportStatusUpdate,
    DailyReportUpdate,
)
from app.services.daily_report import DailyReportService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[DailyReportResponse])
def list_reports(
    project_id: UUID | None = None,
    worker_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_READ)),
):
    service = DailyReportService(DailyReportRepository(db))
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if worker_id:
        filters["worker_id"] = worker_id
    items, _ = service.list(
        tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
    )
    return items


@router.post("/", response_model=DailyReportResponse, status_code=201)
def create_report(
    data: DailyReportCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_CREATE)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{report_id}", response_model=DailyReportResponse)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_READ)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.get(report_id, tenant_id=tenant_id)


@router.put("/{report_id}", response_model=DailyReportResponse)
def update_report(
    report_id: UUID,
    data: DailyReportUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_UPDATE)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.update(report_id, data, tenant_id=tenant_id)


@router.delete("/{report_id}", response_model=Message)
def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_UPDATE)),
):
    service = DailyReportService(DailyReportRepository(db))
    service.delete(report_id, tenant_id=tenant_id)
    return Message(message="Report deleted")


@router.post("/{report_id}/submit", response_model=DailyReportResponse)
def submit_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_CREATE)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.update_status(
        report_id,
        DailyReportStatusUpdate(status="submitted"),
        tenant_id=tenant_id,
        user_id=current_user.id,
    )


@router.post("/{report_id}/approve", response_model=DailyReportResponse)
def approve_report(
    report_id: UUID,
    notes: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_APPROVE)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.update_status(
        report_id,
        DailyReportStatusUpdate(status="approved", notes=notes),
        tenant_id=tenant_id,
        user_id=current_user.id,
    )


@router.post("/{report_id}/reject", response_model=DailyReportResponse)
def reject_report(
    report_id: UUID,
    notes: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_APPROVE)),
):
    service = DailyReportService(DailyReportRepository(db))
    return service.update_status(
        report_id,
        DailyReportStatusUpdate(status="rejected", notes=notes),
        tenant_id=tenant_id,
        user_id=current_user.id,
    )
