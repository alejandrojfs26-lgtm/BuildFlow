
from app.repositories.photo import PhotoRepository
from app.services.base import BaseService


class PhotoService(BaseService):
    def __init__(self, repo: PhotoRepository):
        super().__init__(repo)
