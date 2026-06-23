import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import MaterialUnit
from app.db.base_class import Base, BaseUUIDMixin
from app.db.mixins import TimestampMixin


class Material(BaseUUIDMixin, TimestampMixin, Base):
    __tablename__ = "materials"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[MaterialUnit] = mapped_column(
        String(20), nullable=False, default=MaterialUnit.UNIT
    )
    unit_price: Mapped[float | None] = mapped_column(Float)
    category: Mapped[str | None] = mapped_column(String(100))
    stock: Mapped[float | None] = mapped_column(Float, default=0)
    min_stock: Mapped[float | None] = mapped_column(Float, default=0)
