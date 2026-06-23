from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.export import ExportRepository
from app.schemas.export import ExportCreate, ExportResponse
from app.services.export_service import ExportService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[ExportResponse])
def list_exports(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(get_current_user),
):
    service = ExportService(ExportRepository(db))
    items, _ = service.list(
        tenant_id=tenant_id, skip=skip, limit=limit, order_by="created_at", descending=True
    )
    return items


@router.post("/", response_model=ExportResponse, status_code=201)
def create_export(
    data: ExportCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    service = ExportService(ExportRepository(db))
    return service.create(data, tenant_id=tenant_id, user_id=current_user.id)


@router.get("/{export_id}", response_model=ExportResponse)
def get_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(get_current_user),
):
    service = ExportService(ExportRepository(db))
    return service.get(export_id, tenant_id=tenant_id)


@router.get("/{export_id}/download")
def download_export(
    export_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(get_current_user),
):
    service = ExportService(ExportRepository(db))
    export = service.get(export_id, tenant_id=tenant_id)
    from pathlib import Path

    path = Path(export.file_path)
    media = (
        "text/csv"
        if export.format == "csv"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return FileResponse(path=path, filename=path.name, media_type=media)
