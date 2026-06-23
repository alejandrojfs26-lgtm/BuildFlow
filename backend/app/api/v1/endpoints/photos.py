from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.models.user import User
from app.repositories.daily_report import DailyReportRepository
from app.repositories.photo import PhotoRepository
from app.schemas.photo import PhotoResponse
from app.utils.file_handler import save_file


def _validate_image(file: UploadFile) -> None:
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise ValidationError("Only JPEG, PNG or WebP images are allowed")


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[PhotoResponse])
def list_photos(
    daily_report_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DAILY_REPORT_READ)),
):
    repo = PhotoRepository(db)
    photos = repo.list_by_report(daily_report_id, tenant_id)
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
    _validate_image(file)
    DailyReportRepository(db).get(daily_report_id, tenant_id)

    ext = f".{file.filename.rsplit('.', 1)[-1]}" if file.filename else ".jpg"
    content = file.file.read()
    file_path = save_file(content, f"{tenant_id}/photos", ext)

    repo = PhotoRepository(db)
    photo = repo.create(
        {
            "daily_report_id": daily_report_id,
            "file_path": file_path,
            "file_name": file.filename or "photo",
            "file_type": file.content_type or "image/jpeg",
            "size": len(content),
            "description": description,
            "uploaded_by": current_user.id,
        },
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
    repo = PhotoRepository(db)
    photo = repo.get(photo_id, tenant_id)
    from app.utils.file_handler import delete_file as remove

    remove(photo.file_path)
    repo.delete(photo_id, tenant_id)
    return {"message": "Photo deleted"}
