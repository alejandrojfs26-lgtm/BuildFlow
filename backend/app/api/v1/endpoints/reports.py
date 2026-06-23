from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.report import ReportRepository
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report import ReportService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[ReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.REPORT_READ)),
):
    service = ReportService(ReportRepository(db))
    items, _ = service.list(tenant_id=tenant_id, skip=skip, limit=limit)
    return items


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.REPORT_CREATE)),
):
    service = ReportService(ReportRepository(db))
    return service.create(data, tenant_id=tenant_id, user_id=current_user.id)


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.REPORT_READ)),
):
    service = ReportService(ReportRepository(db))
    return service.get(report_id, tenant_id=tenant_id)


@router.get("/{report_id}/download")
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.REPORT_DOWNLOAD)),
):
    from pathlib import Path

    service = ReportService(ReportRepository(db))
    report = service.get(report_id, tenant_id=tenant_id)

    if not report.file_path:
        raise NotFoundError("Report file", str(report_id))

    path = Path(report.file_path)
    return FileResponse(
        path=path,
        filename=f"{report.name}.pdf",
        media_type="application/pdf",
    )
