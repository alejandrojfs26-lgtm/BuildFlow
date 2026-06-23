from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.constants import ExportStatus


class ExportCreate(BaseModel):
    entity_type: str
    format: str = "csv"


class ExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    entity_type: str
    format: str
    file_path: str | None = None
    status: ExportStatus
    error: str | None = None
    created_by: UUID
    created_at: datetime
