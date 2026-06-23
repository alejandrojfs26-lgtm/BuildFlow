from uuid import UUID

from sqlalchemy import select

from app.models.worker import Worker
from app.repositories.base import BaseRepository


class WorkerRepository(BaseRepository[Worker]):
    def __init__(self, db):
        super().__init__(Worker, db)

    def get_by_dni(self, dni: str, tenant_id: UUID) -> Worker | None:
        return self.db.execute(
            select(Worker).where(
                Worker.dni == dni, Worker.tenant_id == tenant_id
            )
        ).scalar_one_or_none()
