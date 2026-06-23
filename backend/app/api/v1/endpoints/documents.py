from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.document import DocumentService
from app.utils.file_handler import get_absolute_path

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
    service = DocumentService(DocumentRepository(db))
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if category:
        filters["category"] = category
    items, _ = service.list(
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
    service = DocumentService(DocumentRepository(db))
    doc = service.create(
        project_id=project_id,
        name=file.filename or "document",
        content=file.file.read(),
        content_type=file.content_type or "application/octet-stream",
        category=category,
        uploaded_by=current_user.id,
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
    service = DocumentService(DocumentRepository(db))
    file_path, file_type, filename = service.get_download_info(
        document_id, tenant_id
    )
    path = get_absolute_path(file_path)
    return FileResponse(
        path=path,
        media_type=file_type,
        filename=filename,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.DOCUMENT_DELETE)),
):
    service = DocumentService(DocumentRepository(db))
    service.delete(document_id, tenant_id)
    return {"message": "Document deleted"}
