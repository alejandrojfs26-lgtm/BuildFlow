from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.worker import WorkerRepository
from app.schemas.common import Message
from app.schemas.worker import WorkerCreate, WorkerResponse, WorkerUpdate
from app.services.worker import WorkerService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[WorkerResponse])
def list_workers(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_READ)),
):
    service = WorkerService(WorkerRepository(db))
    items, _ = service.list(tenant_id=tenant_id, skip=skip, limit=limit)
    return items


@router.post("/", response_model=WorkerResponse, status_code=201)
def create_worker(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_CREATE)),
):
    service = WorkerService(WorkerRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{worker_id}", response_model=WorkerResponse)
def get_worker(
    worker_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_READ)),
):
    service = WorkerService(WorkerRepository(db))
    return service.get(worker_id, tenant_id=tenant_id)


@router.put("/{worker_id}", response_model=WorkerResponse)
def update_worker(
    worker_id: UUID,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_UPDATE)),
):
    service = WorkerService(WorkerRepository(db))
    return service.update(worker_id, data, tenant_id=tenant_id)


@router.delete("/{worker_id}", response_model=Message)
def delete_worker(
    worker_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.WORKER_DELETE)),
):
    service = WorkerService(WorkerRepository(db))
    service.delete(worker_id, tenant_id=tenant_id)
    return Message(message="Worker deleted")
