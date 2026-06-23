import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DailyReportStatus
from app.db.base_class import Base, BaseUUIDMixin
from app.db.mixins import TimestampMixin


class DailyReport(BaseUUIDMixin, TimestampMixin, Base):
    __tablename__ = "daily_reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_worked: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    overtime_hours: Mapped[float | None] = mapped_column(Float)
    status: Mapped[DailyReportStatus] = mapped_column(
        String(20), nullable=False, default=DailyReportStatus.DRAFT
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    photos = relationship("Photo", back_populates="daily_report", lazy="selectin")
