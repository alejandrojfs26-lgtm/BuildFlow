from uuid import UUID

from sqlalchemy import select

from app.models.photo import Photo
from app.repositories.base import BaseRepository


class PhotoRepository(BaseRepository[Photo]):
    def __init__(self, db):
        super().__init__(Photo, db)

    def list_by_report(self, report_id: UUID, tenant_id: UUID) -> list[Photo]:
        return list(
            self.db.execute(
                select(Photo).where(
                    Photo.daily_report_id == report_id,
                    Photo.tenant_id == tenant_id,
                )
            ).scalars().all()
        )
