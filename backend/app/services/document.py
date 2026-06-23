from uuid import UUID

from app.core.exceptions import ValidationError
from app.repositories.document import DocumentRepository
from app.utils.file_handler import delete_file, save_file

ALLOWED_MIME_TYPES = frozenset({
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
})


class DocumentService:
    def __init__(self, repo: DocumentRepository):
        self.repo = repo

    def list(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
        filters: dict | None = None,
    ) -> tuple[list, int]:
        return self.repo.list(
            tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
        )

    def get(self, document_id: UUID, tenant_id: UUID):
        return self.repo.get(document_id, tenant_id)

    def create(
        self,
        *,
        project_id: UUID,
        name: str,
        content: bytes,
        content_type: str,
        category: str | None,
        uploaded_by: UUID,
        tenant_id: UUID,
    ):
        self._validate(content_type)
        ext = f".{name.rsplit('.', 1)[-1]}" if "." in name else ".bin"
        file_path = save_file(content, f"{tenant_id}/documents", ext)

        return self.repo.create(
            {
                "project_id": project_id,
                "name": name,
                "file_path": file_path,
                "file_type": content_type,
                "size": len(content),
                "category": category,
                "uploaded_by": uploaded_by,
            },
            tenant_id=tenant_id,
        )

    def delete(self, document_id: UUID, tenant_id: UUID) -> None:
        doc = self.repo.get(document_id, tenant_id)
        delete_file(doc.file_path)
        self.repo.delete(document_id, tenant_id)

    def get_download_info(self, document_id: UUID, tenant_id: UUID):
        doc = self.repo.get(document_id, tenant_id)
        return doc.file_path, doc.file_type, doc.name

    @staticmethod
    def _validate(content_type: str) -> None:
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"File type {content_type} not allowed")
