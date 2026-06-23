from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    daily_report_id: UUID
    file_name: str
    file_type: str
    size: int
    description: str | None = None
    uploaded_by: UUID
    created_at: datetime
