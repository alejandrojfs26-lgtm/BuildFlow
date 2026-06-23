from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.common import Message
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project import ProjectService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.PROJECT_READ)),
):
    service = ProjectService(ProjectRepository(db))
    items, _ = service.list(tenant_id=tenant_id, skip=skip, limit=limit)
    return items


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.PROJECT_CREATE)),
):
    service = ProjectService(ProjectRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.PROJECT_READ)),
):
    service = ProjectService(ProjectRepository(db))
    return service.get(project_id, tenant_id=tenant_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.PROJECT_UPDATE)),
):
    service = ProjectService(ProjectRepository(db))
    return service.update(project_id, data, tenant_id=tenant_id)


@router.delete("/{project_id}", response_model=Message)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.PROJECT_DELETE)),
):
    service = ProjectService(ProjectRepository(db))
    service.delete(project_id, tenant_id=tenant_id)
    return Message(message="Project deleted")
