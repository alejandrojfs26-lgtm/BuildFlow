from uuid import UUID

from sqlalchemy import select

from app.models.project import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db):
        super().__init__(Project, db)

    def get_by_code(self, code: str, tenant_id: UUID) -> Project | None:
        return self.db.execute(
            select(Project).where(
                Project.code == code,
                Project.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()
