from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.daily_report import DailyReportRepository
from app.repositories.photo import PhotoRepository
from app.schemas.photo import PhotoResponse
from app.services.photo import PhotoService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[PhotoResponse])
def list_photos(
    daily_report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_READ)),
):
    service = PhotoService(PhotoRepository(db))
    photos = service.list_by_report(daily_report_id, tenant_id)
    return [PhotoResponse.model_validate(p) for p in photos]


@router.post("/", response_model=PhotoResponse, status_code=201)
def upload_photo(
    daily_report_id: UUID,
    file: UploadFile,
    description: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_CREATE)),
):
    DailyReportRepository(db).get(daily_report_id, tenant_id)

    service = PhotoService(PhotoRepository(db))
    photo = service.create(
        daily_report_id=daily_report_id,
        content=file.file.read(),
        content_type=file.content_type or "image/jpeg",
        filename=file.filename or "photo",
        description=description,
        uploaded_by=current_user.id,
        tenant_id=tenant_id,
    )
    return PhotoResponse.model_validate(photo)


@router.delete("/{photo_id}")
def delete_photo(
    photo_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_UPDATE)),
):
    service = PhotoService(PhotoRepository(db))
    service.delete(photo_id, tenant_id)
    return {"message": "Photo deleted"}
