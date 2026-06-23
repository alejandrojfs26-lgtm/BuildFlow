"""Model factories using factory_boy (build strategy — no DB coupling).

Each factory creates a model instance dict (strategy=BUILD).
The test is responsible for persisting via repo/session.
This keeps factories pure and avoids SQLAlchemy session coupling.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import factory

from app.auth.password import hash_password
from app.core.constants import (
    DailyReportStatus,
    ExportStatus,
    MaterialUnit,
    ProjectStatus,
    ReportStatus,
    ReportType,
    Role,
)
from app.models.client import Client
from app.models.daily_report import DailyReport
from app.models.document import Document
from app.models.export import Export
from app.models.material import Material
from app.models.photo import Photo
from app.models.project import Project
from app.models.project_material import ProjectMaterial
from app.models.project_worker import ProjectWorker
from app.models.refresh_token import RefreshToken
from app.models.report import Report
from app.models.tenant import Tenant
from app.models.user import User
from app.models.worker import Worker


class BaseFactory(factory.Factory):
    class Meta:
        abstract = True
        strategy = factory.CREATE_STRATEGY  # BUILD by default

    @classmethod
    def _create(cls, model_class, *args: Any, **kwargs: Any) -> Any:
        """Override: create instance without touching DB."""
        if cls._meta.strategy == factory.CREATE_STRATEGY:
            return model_class(**kwargs)
        return super()._create(model_class, *args, **kwargs)


class TenantFactory(BaseFactory):
    class Meta:
        model = Tenant

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Tenant {n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")
    is_active = True


class UserFactory(BaseFactory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password_hash = factory.LazyFunction(lambda: hash_password("password123"))
    full_name = factory.Sequence(lambda n: f"User {n}")
    role = Role.ADMIN
    is_active = True


class ClientFactory(BaseFactory):
    class Meta:
        model = Client

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Client {n}")


class ProjectFactory(BaseFactory):
    class Meta:
        model = Project

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Project {n}")
    code = factory.Sequence(lambda n: f"PRJ-{n:04d}")
    status = ProjectStatus.PLANNING
    budget = 100000.0


class WorkerFactory(BaseFactory):
    class Meta:
        model = Worker

    id = factory.LazyFunction(uuid.uuid4)
    full_name = factory.Sequence(lambda n: f"Worker {n}")
    dni = factory.Sequence(lambda n: f"{n:08d}")
    is_active = True


class ProjectWorkerFactory(BaseFactory):
    class Meta:
        model = ProjectWorker

    id = factory.LazyFunction(uuid.uuid4)
    start_date = factory.LazyFunction(date.today)
    is_active = True


class MaterialFactory(BaseFactory):
    class Meta:
        model = Material

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Sequence(lambda n: f"Material {n}")
    unit = MaterialUnit.UNIT
    stock = 100.0
    min_stock = 10.0


class ProjectMaterialFactory(BaseFactory):
    class Meta:
        model = ProjectMaterial

    id = factory.LazyFunction(uuid.uuid4)
    quantity = 10.0
    unit_price = 5000.0
    total_price = 50000.0
    date = factory.LazyFunction(date.today)


class DailyReportFactory(BaseFactory):
    class Meta:
        model = DailyReport

    id = factory.LazyFunction(uuid.uuid4)
    date = factory.LazyFunction(date.today)
    hours_worked = 8.0
    description = "Work performed today"
    status = DailyReportStatus.DRAFT


class PhotoFactory(BaseFactory):
    class Meta:
        model = Photo

    id = factory.LazyFunction(uuid.uuid4)
    file_path = "photos/test.jpg"
    file_name = "test.jpg"
    file_type = "image/jpeg"
    size = 1024


class DocumentFactory(BaseFactory):
    class Meta:
        model = Document

    id = factory.LazyFunction(uuid.uuid4)
    name = "document.pdf"
    file_path = "documents/test.pdf"
    file_type = "application/pdf"
    size = 2048


class RefreshTokenFactory(BaseFactory):
    class Meta:
        model = RefreshToken

    id = factory.LazyFunction(uuid.uuid4)
    token_hash = factory.LazyFunction(lambda: uuid.uuid4().hex)
    expires_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )
    is_revoked = False


class ReportFactory(BaseFactory):
    class Meta:
        model = Report

    id = factory.LazyFunction(uuid.uuid4)
    type = ReportType.DAILY_SUMMARY
    name = factory.Sequence(lambda n: f"Report {n}")
    status = ReportStatus.PENDING


class ExportFactory(BaseFactory):
    class Meta:
        model = Export

    id = factory.LazyFunction(uuid.uuid4)
    entity_type = "project"
    format = "csv"
    status = ExportStatus.PENDING
