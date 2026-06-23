from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.assignment import AssignmentRepository
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.schemas.common import Message
from app.services.assignment import AssignmentService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[AssignmentResponse])
def list_assignments(
    project_id: UUID | None = None,
    worker_id: UUID | None = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_READ)),
):
    service = AssignmentService(AssignmentRepository(db))
    filters = {}
    if project_id:
        filters["project_id"] = project_id
    if worker_id:
        filters["worker_id"] = worker_id
    items, _ = service.list(
        tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
    )
    return items


@router.post("/", response_model=AssignmentResponse, status_code=201)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_UPDATE)),
):
    service = AssignmentService(AssignmentRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_READ)),
):
    service = AssignmentService(AssignmentRepository(db))
    return service.get(assignment_id, tenant_id=tenant_id)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: UUID,
    data: AssignmentUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_UPDATE)),
):
    service = AssignmentService(AssignmentRepository(db))
    return service.update(assignment_id, data, tenant_id=tenant_id)


@router.delete("/{assignment_id}", response_model=Message)
def delete_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_DELETE)),
):
    service = AssignmentService(AssignmentRepository(db))
    service.delete(assignment_id, tenant_id=tenant_id)
    return Message(message="Assignment removed")
