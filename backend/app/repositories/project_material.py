from app.models.project_material import ProjectMaterial
from app.repositories.base import BaseRepository


class ProjectMaterialRepository(BaseRepository[ProjectMaterial]):
    def __init__(self, db):
        super().__init__(ProjectMaterial, db)
