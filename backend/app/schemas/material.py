from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import MaterialUnit


class MaterialCreate(BaseModel):
    name: str
    description: str | None = None
    unit: MaterialUnit = MaterialUnit.UNIT
    unit_price: float | None = None
    category: str | None = None
    stock: float | None = 0
    min_stock: float | None = 0


class MaterialUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    unit: MaterialUnit | None = None
    unit_price: float | None = None
    category: str | None = None
    stock: float | None = None
    min_stock: float | None = None


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    unit: MaterialUnit
    unit_price: float | None = None
    category: str | None = None
    stock: float | None = None
    min_stock: float | None = None
    created_at: datetime
    updated_at: datetime
