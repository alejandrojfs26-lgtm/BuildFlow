from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentResponse
from app.utils.file_handler import get_absolute_path, save_file


def _validate_file(file: UploadFile) -> None:
    allowed = (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    if file.content_type not in allowed:
        raise ValidationError(f"File type {file.content_type} not allowed")


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    project_id: UUID | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DOCUMENT_READ)),
):
    repo = DocumentRepository(db)
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if category:
        filters["category"] = category
    items, _ = repo.list(
        tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
    )
    return [DocumentResponse.model_validate(d) for d in items]


@router.post("/", response_model=DocumentResponse, status_code=201)
def upload_document(
    project_id: UUID,
    file: UploadFile,
    category: str | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_permissions(Permission.DOCUMENT_UPLOAD)),
):
    _validate_file(file)

    ext = f".{file.filename.rsplit('.', 1)[-1]}" if file.filename else ".bin"
    content = file.file.read()
    file_path = save_file(content, f"{tenant_id}/documents", ext)

    repo = DocumentRepository(db)
    doc = repo.create(
        {
            "project_id": project_id,
            "name": file.filename or "document",
            "file_path": file_path,
            "file_type": file.content_type or "application/octet-stream",
            "size": len(content),
            "category": category,
            "uploaded_by": current_user.id,
        },
        tenant_id=tenant_id,
    )
    return DocumentResponse.model_validate(doc)


@router.get("/{document_id}")
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DOCUMENT_READ)),
):
    repo = DocumentRepository(db)
    doc = repo.get(document_id, tenant_id)
    path = get_absolute_path(doc.file_path)
    return FileResponse(
        path=path,
        media_type=doc.file_type,
        filename=doc.name,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DOCUMENT_DELETE)),
):
    repo = DocumentRepository(db)
    doc = repo.get(document_id, tenant_id)
    from app.utils.file_handler import delete_file as remove

    remove(doc.file_path)
    repo.delete(document_id, tenant_id)
    return {"message": "Document deleted"}
