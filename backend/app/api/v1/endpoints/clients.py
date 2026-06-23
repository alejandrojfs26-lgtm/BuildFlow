from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.client import ClientRepository
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import Message
from app.services.client import ClientService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.CLIENT_READ)),
):
    service = ClientService(ClientRepository(db))
    items, _ = service.list(tenant_id=tenant_id, skip=skip, limit=limit)
    return items


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.CLIENT_CREATE)),
):
    service = ClientService(ClientRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.CLIENT_READ)),
):
    service = ClientService(ClientRepository(db))
    return service.get(client_id, tenant_id=tenant_id)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.CLIENT_UPDATE)),
):
    service = ClientService(ClientRepository(db))
    return service.update(client_id, data, tenant_id=tenant_id)


@router.delete("/{client_id}", response_model=Message)
def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.CLIENT_DELETE)),
):
    service = ClientService(ClientRepository(db))
    service.delete(client_id, tenant_id=tenant_id)
    return Message(message="Client deleted")
