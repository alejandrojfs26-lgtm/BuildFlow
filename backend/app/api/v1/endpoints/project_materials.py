from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.material import MaterialRepository
from app.repositories.project_material import ProjectMaterialRepository
from app.schemas.common import Message
from app.schemas.project_material import (
    ProjectMaterialCreate,
    ProjectMaterialResponse,
    ProjectMaterialUpdate,
)
from app.services.project_material import ProjectMaterialService

router = APIRouter(dependencies=[Depends(get_current_user)])


def _build_service(db: Session) -> ProjectMaterialService:
    return ProjectMaterialService(
        ProjectMaterialRepository(db),
        MaterialRepository(db),
    )


@router.get("/", response_model=list[ProjectMaterialResponse])
def list_project_materials(
    project_id: UUID | None = None,
    material_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_READ)),
):
    service = _build_service(db)
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if material_id:
        filters["material_id"] = material_id
    items, _ = service.list(
        tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
    )
    return items


@router.post("/", response_model=ProjectMaterialResponse, status_code=201)
def create_project_material(
    data: ProjectMaterialCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_UPDATE)),
):
    service = _build_service(db)
    return service.create(data, tenant_id=tenant_id)


@router.get("/{entry_id}", response_model=ProjectMaterialResponse)
def get_project_material(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_READ)),
):
    service = _build_service(db)
    return service.get(entry_id, tenant_id=tenant_id)


@router.put("/{entry_id}", response_model=ProjectMaterialResponse)
def update_project_material(
    entry_id: UUID,
    data: ProjectMaterialUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_UPDATE)),
):
    service = _build_service(db)
    return service.update(entry_id, data, tenant_id=tenant_id)


@router.delete("/{entry_id}", response_model=Message)
def delete_project_material(
    entry_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_DELETE)),
):
    service = _build_service(db)
    service.delete(entry_id, tenant_id=tenant_id)
    return Message(message="Entry deleted")
