from uuid import UUID

from app.core.exceptions import ValidationError
from app.repositories.photo import PhotoRepository
from app.utils.file_handler import delete_file, save_file

ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


class PhotoService:
    def __init__(self, repo: PhotoRepository):
        self.repo = repo

    def list_by_report(
        self, daily_report_id: UUID, tenant_id: UUID
    ) -> list:
        return self.repo.list_by_report(daily_report_id, tenant_id)

    def create(
        self,
        *,
        daily_report_id: UUID,
        content: bytes,
        content_type: str,
        filename: str,
        description: str | None,
        uploaded_by: UUID,
        tenant_id: UUID,
    ):
        self._validate(content_type)
        ext = f".{filename.rsplit('.', 1)[-1]}" if "." in filename else ".jpg"
        file_path = save_file(content, f"{tenant_id}/photos", ext)

        return self.repo.create(
            {
                "daily_report_id": daily_report_id,
                "file_path": file_path,
                "file_name": filename,
                "file_type": content_type,
                "size": len(content),
                "description": description,
                "uploaded_by": uploaded_by,
            },
            tenant_id=tenant_id,
        )

    def get(self, photo_id: UUID, tenant_id: UUID):
        return self.repo.get(photo_id, tenant_id)

    def delete(self, photo_id: UUID, tenant_id: UUID) -> None:
        photo = self.repo.get(photo_id, tenant_id)
        delete_file(photo.file_path)
        self.repo.delete(photo_id, tenant_id)

    @staticmethod
    def _validate(content_type: str) -> None:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                "Only JPEG, PNG or WebP images are allowed"
            )
