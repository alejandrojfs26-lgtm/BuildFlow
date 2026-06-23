from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectMaterialCreate(BaseModel):
    project_id: UUID
    material_id: UUID
    quantity: float
    unit_price: float
    date: date
    notes: str | None = None


class ProjectMaterialUpdate(BaseModel):
    quantity: float | None = None
    unit_price: float | None = None
    notes: str | None = None


class ProjectMaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    material_id: UUID
    quantity: float
    unit_price: float
    total_price: float
    date: date
    notes: str | None = None
    created_at: datetime
