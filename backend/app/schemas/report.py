from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import ReportStatus, ReportType


class ReportCreate(BaseModel):
    project_id: UUID | None = None
    type: ReportType
    name: str
    parameters: dict | None = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID | None = None
    type: ReportType
    name: str
    parameters: dict | None = None
    data: dict | None = None
    file_path: str | None = None
    status: ReportStatus
    error: str | None = None
    generated_by: UUID
    created_at: datetime
