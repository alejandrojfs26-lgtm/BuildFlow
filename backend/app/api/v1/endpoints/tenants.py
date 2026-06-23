from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.tenant import TenantRepository
from app.schemas.common import Message
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.services.tenant import TenantService

router = APIRouter()


@router.get("/", response_model=list[TenantResponse])
def list_tenants(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    service = TenantService(TenantRepository(db))
    items, _ = service.list(skip=skip, limit=limit)
    return items


@router.post("/", response_model=TenantResponse, status_code=201)
def create_tenant(
    data: TenantCreate,
    db: Session = Depends(get_db),
):
    service = TenantService(TenantRepository(db))
    return service.create(data)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
):
    service = TenantService(TenantRepository(db))
    return service.get(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: UUID,
    data: TenantUpdate,
    db: Session = Depends(get_db),
):
    service = TenantService(TenantRepository(db))
    return service.update(tenant_id, data)


@router.delete("/{tenant_id}", response_model=Message)
def delete_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
):
    service = TenantService(TenantRepository(db))
    service.delete(tenant_id)
    return Message(message="Tenant deleted")
