from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkerCreate(BaseModel):
    full_name: str
    dni: str
    phone: str | None = None
    email: str | None = None
    position: str | None = None
    specialty: str | None = None
    hire_date: date | None = None
    hourly_rate: float | None = None
    is_active: bool = True


class WorkerUpdate(BaseModel):
    full_name: str | None = None
    dni: str | None = None
    phone: str | None = None
    email: str | None = None
    position: str | None = None
    specialty: str | None = None
    hire_date: date | None = None
    hourly_rate: float | None = None
    is_active: bool | None = None


class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID | None = None
    full_name: str
    dni: str
    phone: str | None = None
    email: str | None = None
    position: str | None = None
    specialty: str | None = None
    hire_date: date | None = None
    hourly_rate: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
