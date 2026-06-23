from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    project_id: UUID
    category: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    name: str
    file_type: str
    size: int
    category: str | None = None
    uploaded_by: UUID
    created_at: datetime
