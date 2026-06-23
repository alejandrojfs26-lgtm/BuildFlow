from uuid import UUID

from app.core.exceptions import ValidationError
from app.repositories.material import MaterialRepository
from app.repositories.project_material import ProjectMaterialRepository
from app.schemas.project_material import ProjectMaterialCreate
from app.services.base import BaseService


class ProjectMaterialService(BaseService):
    def __init__(self, repo: ProjectMaterialRepository):
        super().__init__(repo)

    def create(self, data: ProjectMaterialCreate, tenant_id: UUID, db) -> ...:
        material_repo = MaterialRepository(db)
        material = material_repo.get(data.material_id, tenant_id)

        if data.quantity <= 0:
            raise ValidationError("quantity must be positive")

        if material.stock is not None and data.quantity > material.stock:
            raise ValidationError(
                f"Insufficient stock: {material.stock} {material.unit} available, "
                f"{data.quantity} requested"
            )

        total = round(data.quantity * data.unit_price, 2)
        entry = self.repo.create(
            {**data.model_dump(), "total_price": total},
            tenant_id=tenant_id,
        )

        if material.stock is not None:
            material_repo.update(
                material.id,
                {"stock": material.stock - data.quantity},
                tenant_id=tenant_id,
            )

        return entry
