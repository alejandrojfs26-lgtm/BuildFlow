import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ReportStatus, ReportType
from app.db.base_class import Base, BaseUUIDMixin


class Report(BaseUUIDMixin, Base):
    __tablename__ = "reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    type: Mapped[ReportType] = mapped_column(
        String(30), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    data: Mapped[dict | None] = mapped_column(JSONB)
    file_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ReportStatus] = mapped_column(
        String(20), nullable=False, default=ReportStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(Text)
    generated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
