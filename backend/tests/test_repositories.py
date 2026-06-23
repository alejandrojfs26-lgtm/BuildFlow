"""Repository tests — verify persistence, tenant scoping, and error handling.

Factories create model instances (no DB). Tests persist via session.add/flush.
"""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.client import ClientRepository
from app.repositories.daily_report import DailyReportRepository
from app.repositories.material import MaterialRepository
from app.repositories.user import UserRepository
from app.schemas.client import ClientCreate
from app.schemas.material import MaterialCreate
from tests.factories import (
    ClientFactory,
    DailyReportFactory,
    MaterialFactory,
    ProjectFactory,
    TenantFactory,
    UserFactory,
    WorkerFactory,
)


@pytest.fixture
def tenant(db_session: Session):
    obj = TenantFactory.create()
    db_session.add(obj)
    db_session.flush()
    return obj


@pytest.fixture
def other_tenant(db_session: Session):
    obj = TenantFactory.create()
    db_session.add(obj)
    db_session.flush()
    return obj


# ---------------------------------------------------------------------------
# BaseRepository — CRUD
# ---------------------------------------------------------------------------


class TestBaseRepositoryGet:
    def test_get_existing(self, db_session: Session, tenant) -> None:
        client = ClientFactory.create(tenant_id=tenant.id)
        db_session.add(client)
        db_session.flush()

        repo = ClientRepository(db_session)
        found = repo.get(client.id, tenant_id=tenant.id)
        assert found.id == client.id

    def test_get_not_found(self, db_session: Session) -> None:
        repo = ClientRepository(db_session)
        with pytest.raises(NotFoundError):
            repo.get(uuid4())

    def test_get_scoped_to_tenant(
        self, db_session: Session, tenant, other_tenant
    ) -> None:
        client = ClientFactory.create(tenant_id=tenant.id)
        db_session.add(client)
        db_session.flush()

        repo = ClientRepository(db_session)
        assert repo.get(client.id, tenant_id=tenant.id)
        with pytest.raises(NotFoundError):
            repo.get(client.id, tenant_id=other_tenant.id)

    def test_get_without_tenant_scope_finds_any(
        self, db_session: Session, tenant, other_tenant
    ) -> None:
        client = ClientFactory.create(tenant_id=tenant.id)
        db_session.add(client)
        db_session.flush()

        repo = ClientRepository(db_session)
        found = repo.get(client.id)
        assert found.id == client.id
        assert found.tenant_id == tenant.id


class TestBaseRepositoryCreate:
    def test_create_with_tenant(self, db_session: Session, tenant) -> None:
        repo = ClientRepository(db_session)
        client = repo.create(
            ClientCreate(name="New Client"),
            tenant_id=tenant.id,
        )
        assert client.tenant_id == tenant.id
        assert client.name == "New Client"

    def test_create_without_tenant_for_tenantless_model(
        self, db_session: Session
    ) -> None:
        repo = TenantRepository(db_session)
        tenant = repo.create(
            TenantCreate(name="Orphan Tenant", slug="orphan"),
        )
        assert tenant.name == "Orphan Tenant"


class TestBaseRepositoryList:
    def test_list_pagination(self, db_session: Session, tenant) -> None:
        for i in range(5):
            db_session.add(ClientFactory.create(name=f"C{i}", tenant_id=tenant.id))
        db_session.flush()

        repo = ClientRepository(db_session)
        page1, total = repo.list(tenant_id=tenant.id, skip=0, limit=2)
        assert len(page1) == 2
        assert total == 5

        page2, _ = repo.list(tenant_id=tenant.id, skip=2, limit=2)
        assert len(page2) == 2

    def test_list_filters(self, db_session: Session, tenant) -> None:
        db_session.add_all([
            ClientFactory.create(name="Alpha", tenant_id=tenant.id),
            ClientFactory.create(name="Beta", tenant_id=tenant.id),
        ])
        db_session.flush()

        repo = ClientRepository(db_session)
        items, total = repo.list(
            tenant_id=tenant.id, filters={"name": "Beta"}
        )
        assert total == 1
        assert items[0].name == "Beta"

    def test_list_tenant_isolation(
        self, db_session: Session, tenant, other_tenant
    ) -> None:
        db_session.add_all([
            ClientFactory.create(tenant_id=tenant.id) for _ in range(3)
        ])
        db_session.add_all([
            ClientFactory.create(tenant_id=other_tenant.id) for _ in range(2)
        ])
        db_session.flush()

        repo = ClientRepository(db_session)
        _, t1_total = repo.list(tenant_id=tenant.id)
        _, t2_total = repo.list(tenant_id=other_tenant.id)
        assert t1_total == 3
        assert t2_total == 2


class TestBaseRepositoryUpdate:
    def test_update_partial(self, db_session: Session, tenant) -> None:
        material = MaterialFactory.create(name="Old Name", tenant_id=tenant.id)
        db_session.add(material)
        db_session.flush()

        repo = MaterialRepository(db_session)
        updated = repo.update(
            material.id,
            {"name": "New Name"},
            tenant_id=tenant.id,
        )
        assert updated.name == "New Name"
        assert updated.unit == material.unit

    def test_update_not_found(self, db_session: Session) -> None:
        repo = MaterialRepository(db_session)
        with pytest.raises(NotFoundError):
            repo.update(uuid4(), {"name": "x"})


class TestBaseRepositoryDelete:
    def test_delete_then_get_raises(self, db_session: Session, tenant) -> None:
        material = MaterialFactory.create(tenant_id=tenant.id)
        db_session.add(material)
        db_session.flush()

        repo = MaterialRepository(db_session)
        repo.delete(material.id, tenant_id=tenant.id)
        with pytest.raises(NotFoundError):
            repo.get(material.id, tenant_id=tenant.id)

    def test_delete_not_found(self, db_session: Session) -> None:
        repo = MaterialRepository(db_session)
        with pytest.raises(NotFoundError):
            repo.delete(uuid4())


class TestBaseRepositoryExistsAndUnique:
    def test_exists(self, db_session: Session, tenant) -> None:
        db_session.add(MaterialFactory.create(name="Cement", tenant_id=tenant.id))
        db_session.flush()

        repo = MaterialRepository(db_session)
        assert repo.exists("name", "Cement", tenant_id=tenant.id)
        assert not repo.exists("name", "Steel", tenant_id=tenant.id)

    def test_assert_unique_raises_conflict(
        self, db_session: Session, tenant
    ) -> None:
        db_session.add(MaterialFactory.create(name="Brick", tenant_id=tenant.id))
        db_session.flush()

        repo = MaterialRepository(db_session)
        with pytest.raises(ConflictError):
            repo.assert_unique("name", "Brick", tenant_id=tenant.id)


# ---------------------------------------------------------------------------
# Custom repository queries
# ---------------------------------------------------------------------------


class TestDailyReportRepository:
    def test_get_by_worker_date_found(
        self, db_session: Session
    ) -> None:
        tenant_obj = TenantFactory.create()
        db_session.add(tenant_obj)
        client = ClientFactory.create(tenant_id=tenant_obj.id)
        db_session.add(client)
        project = ProjectFactory.create(
            tenant_id=tenant_obj.id, client_id=client.id
        )
        db_session.add(project)
        worker = WorkerFactory.create(tenant_id=tenant_obj.id)
        db_session.add(worker)
        report = DailyReportFactory.create(
            tenant_id=tenant_obj.id,
            project_id=project.id,
            worker_id=worker.id,
        )
        db_session.add(report)
        db_session.flush()

        repo = DailyReportRepository(db_session)
        found = repo.get_by_worker_date(
            worker.id, report.date, tenant_obj.id
        )
        assert found is not None
        assert found.id == report.id

    def test_get_by_worker_date_not_found(self, db_session: Session) -> None:
        tenant_obj = TenantFactory.create()
        db_session.add(tenant_obj)
        worker = WorkerFactory.create(tenant_id=tenant_obj.id)
        db_session.add(worker)
        db_session.flush()

        repo = DailyReportRepository(db_session)
        found = repo.get_by_worker_date(
            worker.id, date.today(), tenant_obj.id
        )
        assert found is None


class TestUserRepository:
    def test_get_by_email(self, db_session: Session) -> None:
        tenant_obj = TenantFactory.create()
        db_session.add(tenant_obj)
        user = UserFactory.create(
            email="unique@test.com", tenant_id=tenant_obj.id
        )
        db_session.add(user)
        db_session.flush()

        repo = UserRepository(db_session)
        assert repo.get_by_email("unique@test.com") is not None
        assert repo.get_by_email("nonexistent@test.com") is None

    def test_get_by_id(self, db_session: Session) -> None:
        tenant_obj = TenantFactory.create()
        db_session.add(tenant_obj)
        user = UserFactory.create(tenant_id=tenant_obj.id)
        db_session.add(user)
        db_session.flush()

        repo = UserRepository(db_session)
        assert repo.get_by_id(user.id) is not None
        assert repo.get_by_id(uuid4()) is None


# Late imports to avoid circular dependencies with fixtures
from app.repositories.tenant import TenantRepository  # noqa: E402
from app.schemas.tenant import TenantCreate  # noqa: E402
