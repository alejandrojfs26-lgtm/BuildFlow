from uuid import UUID

from sqlalchemy import select

from app.models.project_worker import ProjectWorker
from app.repositories.base import BaseRepository


class AssignmentRepository(BaseRepository[ProjectWorker]):
    def __init__(self, db):
        super().__init__(ProjectWorker, db)

    def get_by_project_and_worker(
        self, project_id: UUID, worker_id: UUID, tenant_id: UUID
    ) -> ProjectWorker | None:
        return self.db.execute(
            select(ProjectWorker).where(
                ProjectWorker.project_id == project_id,
                ProjectWorker.worker_id == worker_id,
                ProjectWorker.tenant_id == tenant_id,
            )
        ).scalar_one_or_none()

    def list_by_project(
        self, project_id: UUID, tenant_id: UUID
    ) -> list[ProjectWorker]:
        query = select(ProjectWorker).where(
            ProjectWorker.project_id == project_id,
            ProjectWorker.tenant_id == tenant_id,
        )
        return list(self.db.execute(query).scalars().all())

    def list_by_worker(
        self, worker_id: UUID, tenant_id: UUID
    ) -> list[ProjectWorker]:
        query = select(ProjectWorker).where(
            ProjectWorker.worker_id == worker_id,
            ProjectWorker.tenant_id == tenant_id,
        )
        return list(self.db.execute(query).scalars().all())
