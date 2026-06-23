from app.repositories.document import DocumentRepository
from app.services.base import BaseService


class DocumentService(BaseService):
    def __init__(self, repo: DocumentRepository):
        super().__init__(repo)
