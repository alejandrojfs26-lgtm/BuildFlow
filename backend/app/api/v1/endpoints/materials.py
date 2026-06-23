from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user
from app.auth.permissions import require_permissions
from app.core.constants import Permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.material import MaterialRepository
from app.schemas.common import Message
from app.schemas.material import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.material import MaterialService

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[MaterialResponse])
def list_materials(
    category: str | None = None,
    low_stock: bool = False,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_READ)),
):
    service = MaterialService(MaterialRepository(db))
    filters = {}
    if category:
        filters["category"] = category
    items, total = service.list(
        tenant_id=tenant_id, skip=skip, limit=limit, filters=filters
    )
    if low_stock:
        items = [m for m in items if m.min_stock is not None and (m.stock or 0) <= m.min_stock]
    return items


@router.post("/", response_model=MaterialResponse, status_code=201)
def create_material(
    data: MaterialCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_CREATE)),
):
    service = MaterialService(MaterialRepository(db))
    return service.create(data, tenant_id=tenant_id)


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_READ)),
):
    service = MaterialService(MaterialRepository(db))
    return service.get(material_id, tenant_id=tenant_id)


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: UUID,
    data: MaterialUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_UPDATE)),
):
    service = MaterialService(MaterialRepository(db))
    return service.update(material_id, data, tenant_id=tenant_id)


@router.delete("/{material_id}", response_model=Message)
def delete_material(
    material_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _: User = Depends(require_permissions(Permission.MATERIAL_DELETE)),
):
    service = MaterialService(MaterialRepository(db))
    service.delete(material_id, tenant_id=tenant_id)
    return Message(message="Material deleted")
