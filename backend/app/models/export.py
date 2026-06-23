import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ExportStatus
from app.db.base_class import Base, BaseUUIDMixin


class Export(BaseUUIDMixin, Base):
    __tablename__ = "exports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    file_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ExportStatus] = mapped_column(
        String(20), nullable=False, default=ExportStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
