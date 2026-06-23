from app.repositories.client import ClientRepository
from app.services.base import BaseService


class ClientService(BaseService):
    def __init__(self, repo: ClientRepository):
        super().__init__(repo)
