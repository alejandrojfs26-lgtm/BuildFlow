from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.constants import DailyReportStatus


class DailyReportCreate(BaseModel):
    project_id: UUID
    worker_id: UUID
    date: date
    hours_worked: float
    description: str
    overtime_hours: float | None = None

    @field_validator("hours_worked")
    @classmethod
    def max_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("hours_worked must be positive")
        if v > 24:
            raise ValueError("hours_worked cannot exceed 24")
        return v

    @field_validator("date")
    @classmethod
    def not_future(cls, v: date) -> date:
        from datetime import date as d

        if v > d.today():
            raise ValueError("date cannot be in the future")
        return v


class DailyReportUpdate(BaseModel):
    hours_worked: float | None = None
    description: str | None = None
    overtime_hours: float | None = None
    notes: str | None = None

    @field_validator("hours_worked")
    @classmethod
    def max_hours(cls, v: float | None) -> float | None:
        if v is not None and (v <= 0 or v > 24):
            raise ValueError("hours_worked must be between 0 and 24")
        return v


class DailyReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    worker_id: UUID
    date: date
    hours_worked: float
    description: str
    overtime_hours: float | None = None
    status: DailyReportStatus
    approved_by: UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DailyReportStatusUpdate(BaseModel):
    status: DailyReportStatus
    notes: str | None = None
