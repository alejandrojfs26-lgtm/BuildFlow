from app.models.export import Export
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[Export]):
    def __init__(self, db):
        super().__init__(Export, db)
