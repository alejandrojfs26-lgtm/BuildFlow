from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import ProjectStatus


class ProjectCreate(BaseModel):
    client_id: UUID
    name: str
    code: str
    description: str | None = None
    address: str | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None


class ProjectUpdate(BaseModel):
    client_id: UUID | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None
    address: str | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    name: str
    code: str
    description: str | None = None
    address: str | None = None
    status: ProjectStatus
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    created_at: datetime
    updated_at: datetime
