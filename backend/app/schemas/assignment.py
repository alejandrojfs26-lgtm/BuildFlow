from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class AssignmentCreate(BaseModel):
    project_id: UUID
    worker_id: UUID
    role: str | None = None
    start_date: date
    end_date: date | None = None
    hourly_rate: float | None = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date | None, info) -> date | None:
        if v and info.data.get("start_date") and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v


class AssignmentUpdate(BaseModel):
    role: str | None = None
    end_date: date | None = None
    hourly_rate: float | None = None
    is_active: bool | None = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    worker_id: UUID
    role: str | None = None
    start_date: date
    end_date: date | None = None
    hourly_rate: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
