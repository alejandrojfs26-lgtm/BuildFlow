"""Service tests — verify business logic with mocked repositories.

Pattern: Service ← Mock(repo) ← pytest mocks
Benefit: Pure unit tests, no DB, 100x faster, exact error-path coverage.
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import create_autospec
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.constants import DailyReportStatus
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.repositories.client import ClientRepository
from app.repositories.daily_report import DailyReportRepository
from app.repositories.material import MaterialRepository
from app.repositories.project_material import ProjectMaterialRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.daily_report import DailyReportCreate, DailyReportStatusUpdate
from app.schemas.project_material import ProjectMaterialCreate
from app.services.auth import AuthService
from app.services.daily_report import DailyReportService
from app.services.project_material import ProjectMaterialService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
USER_ID = uuid4()


def mock_repo(cls, name: str | None = None):
    return create_autospec(cls, instance=True, spec_set=True)


def fake_user(**overrides):
    from types import SimpleNamespace

    attrs = {
        "id": USER_ID,
        "tenant_id": TENANT_ID,
        "email": "admin@test.com",
        "password_hash": "$2b$12$" + "x" * 50,
        "full_name": "Admin",
        "role": "admin",
        "is_active": True,
    }
    attrs.update(overrides)
    return SimpleNamespace(**attrs)


def fake_material(**overrides):
    from types import SimpleNamespace

    attrs = {
        "id": uuid4(),
        "name": "Cement",
        "unit": "kg",
        "stock": 100.0,
        "min_stock": 10.0,
    }
    attrs.update(overrides)
    return SimpleNamespace(**attrs)


# ---------------------------------------------------------------------------
# ProjectMaterialService
# ---------------------------------------------------------------------------


class TestProjectMaterialService:
    def test_create_deducts_stock(self) -> None:
        pm_repo = mock_repo(ProjectMaterialRepository)
        mat_repo = mock_repo(MaterialRepository)
        material = fake_material(stock=100.0)
        mat_repo.get.return_value = material

        service = ProjectMaterialService(pm_repo, mat_repo)

        entry = fake_material()
        pm_repo.create.return_value = entry

        result = service.create(
            ProjectMaterialCreate(
                project_id=uuid4(),
                material_id=material.id,
                quantity=10,
                unit_price=5000,
                date=date.today(),
            ),
            tenant_id=TENANT_ID,
        )

        mat_repo.update.assert_called_once_with(
            material.id,
            {"stock": 90.0},
            tenant_id=TENANT_ID,
        )
        assert result == entry

    def test_create_insufficient_stock_raises(self) -> None:
        pm_repo = mock_repo(ProjectMaterialRepository)
        mat_repo = mock_repo(MaterialRepository)
        mat_repo.get.return_value = fake_material(stock=5.0)

        service = ProjectMaterialService(pm_repo, mat_repo)

        with pytest.raises(ValidationError, match="Insufficient stock"):
            service.create(
                ProjectMaterialCreate(
                    project_id=uuid4(),
                    material_id=uuid4(),
                    quantity=10,
                    unit_price=100,
                    date=date.today(),
                ),
                tenant_id=TENANT_ID,
            )

    def test_create_null_stock_skips_update(self) -> None:
        pm_repo = mock_repo(ProjectMaterialRepository)
        mat_repo = mock_repo(MaterialRepository)
        mat_repo.get.return_value = fake_material(stock=None)

        service = ProjectMaterialService(pm_repo, mat_repo)
        pm_repo.create.return_value = fake_material()

        service.create(
            ProjectMaterialCreate(
                project_id=uuid4(),
                material_id=uuid4(),
                quantity=10,
                unit_price=100,
                date=date.today(),
            ),
            tenant_id=TENANT_ID,
        )

        mat_repo.update.assert_not_called()

    def test_create_negative_quantity_raises(self) -> None:
        pm_repo = mock_repo(ProjectMaterialRepository)
        mat_repo = mock_repo(MaterialRepository)
        mat_repo.get.return_value = fake_material(stock=100)

        service = ProjectMaterialService(pm_repo, mat_repo)

        with pytest.raises(ValidationError, match="positive"):
            service.create(
                ProjectMaterialCreate(
                    project_id=uuid4(),
                    material_id=uuid4(),
                    quantity=-1,
                    unit_price=100,
                    date=date.today(),
                ),
                tenant_id=TENANT_ID,
            )


# ---------------------------------------------------------------------------
# DailyReportService
# ---------------------------------------------------------------------------


class TestDailyReportService:
    def test_create_first_report_succeeds(self) -> None:
        repo = mock_repo(DailyReportRepository)
        repo.get_by_worker_date.return_value = None

        service = DailyReportService(repo)
        data = DailyReportCreate(
            project_id=uuid4(),
            worker_id=uuid4(),
            date=date.today(),
            hours_worked=8,
            description="Good work",
        )

        service.create(data, tenant_id=TENANT_ID)
        repo.create.assert_called_once_with(data, tenant_id=TENANT_ID)

    def test_create_duplicate_raises(self) -> None:
        repo = mock_repo(DailyReportRepository)
        repo.get_by_worker_date.return_value = fake_material()

        service = DailyReportService(repo)

        with pytest.raises(ConflictError, match="already exists"):
            service.create(
                DailyReportCreate(
                    project_id=uuid4(),
                    worker_id=uuid4(),
                    date=date.today(),
                    hours_worked=8,
                    description="Duplicate",
                ),
                tenant_id=TENANT_ID,
            )


class TestDailyReportStatusTransition:
    def setup_method(self):
        self.repo = mock_repo(DailyReportRepository)
        self.service = DailyReportService(self.repo)
        self.report_id = uuid4()

    def _make_report(self, status: DailyReportStatus):
        return fake_material(id=self.report_id, status=status, approved_by=None)

    def test_draft_to_submitted(self) -> None:
        self.repo.get.return_value = self._make_report(DailyReportStatus.DRAFT)
        self.service.update_status(
            self.report_id,
            DailyReportStatusUpdate(status="submitted"),
            tenant_id=TENANT_ID,
            user_id=USER_ID,
        )
        self.repo.update.assert_called_once()

    def test_submitted_to_approved(self) -> None:
        self.repo.get.return_value = self._make_report(DailyReportStatus.SUBMITTED)
        self.service.update_status(
            self.report_id,
            DailyReportStatusUpdate(status="approved"),
            tenant_id=TENANT_ID,
            user_id=USER_ID,
        )
        self.repo.update.assert_called_once()

    def test_draft_to_approved_raises(self) -> None:
        self.repo.get.return_value = self._make_report(DailyReportStatus.DRAFT)
        with pytest.raises(ValidationError):
            self.service.update_status(
                self.report_id,
                DailyReportStatusUpdate(status="approved"),
                tenant_id=TENANT_ID,
                user_id=USER_ID,
            )

    def test_approved_to_submitted_raises(self) -> None:
        self.repo.get.return_value = self._make_report(DailyReportStatus.APPROVED)
        with pytest.raises(ValidationError):
            self.service.update_status(
                self.report_id,
                DailyReportStatusUpdate(status="submitted"),
                tenant_id=TENANT_ID,
                user_id=USER_ID,
            )


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


class TestAuthServiceRegister:
    def test_register_success(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        user_repo.get_by_email.return_value = None
        tenant_repo.get_by_slug.return_value = None

        tenant_repo.create.return_value = fake_user(id=uuid4())
        user_repo.create.return_value = fake_user()

        service = AuthService(user_repo, tenant_repo, refresh_repo)

        access, refresh, user_data = service.register(
            RegisterRequest(
                company_name="TestCo",
                company_slug="testco",
                email="admin@testco.com",
                password="Str0ng!Pass",
                full_name="Admin",
            )
        )

        assert isinstance(access, str)
        assert isinstance(refresh, str)
        assert user_data["email"] == "admin@test.com"
        tenant_repo.create.assert_called_once()
        user_repo.create.assert_called_once()
        refresh_repo.create.assert_called_once()

    def test_register_duplicate_email_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)
        user_repo.get_by_email.return_value = fake_user()

        service = AuthService(user_repo, tenant_repo, refresh_repo)

        with pytest.raises(ConflictError, match="Email already registered"):
            service.register(
                RegisterRequest(
                    company_name="T",
                    company_slug="t",
                    email="dup@test.com",
                    password="Str0ng!Pass",
                    full_name="Admin",
                )
            )

    def test_register_duplicate_slug_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        user_repo.get_by_email.return_value = None
        tenant_repo.get_by_slug.return_value = fake_user()

        service = AuthService(user_repo, tenant_repo, refresh_repo)

        with pytest.raises(ConflictError, match="slug already taken"):
            service.register(
                RegisterRequest(
                    company_name="T",
                    company_slug="taken-slug",
                    email="a@test.com",
                    password="Str0ng!Pass",
                    full_name="Admin",
                )
            )


class TestAuthServiceLogin:
    def test_login_success(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.password import hash_password

        user_repo.get_by_email.return_value = fake_user(
            password_hash=hash_password("correct-pass")
        )
        tenant_repo.get_by_id.return_value = fake_user(is_active=True)

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        access, refresh, user_data = service.login("a@b.com", "correct-pass")

        assert isinstance(access, str)
        assert isinstance(refresh, str)

    def test_login_wrong_password_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.password import hash_password

        user_repo.get_by_email.return_value = fake_user(
            password_hash=hash_password("real-pass")
        )

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        with pytest.raises(UnauthorizedError, match="Invalid email or password"):
            service.login("a@b.com", "wrong-pass")

    def test_login_inactive_user_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.password import hash_password

        user_repo.get_by_email.return_value = fake_user(
            is_active=False,
            password_hash=hash_password("x"),
        )

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        with pytest.raises(UnauthorizedError, match="inactive"):
            service.login("a@b.com", "x")

    def test_login_inactive_tenant_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.password import hash_password

        user_repo.get_by_email.return_value = fake_user(
            password_hash=hash_password("pass")
        )
        tenant_repo.get_by_id.return_value = fake_user(is_active=False)

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        with pytest.raises(UnauthorizedError, match="Tenant is inactive"):
            service.login("a@b.com", "pass")


class TestAuthServiceRefresh:
    def test_refresh_revokes_old_token(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.jwt import create_refresh_token

        old_token = create_refresh_token(USER_ID)
        from hashlib import sha256

        token_hash = sha256(old_token.encode()).hexdigest()
        stored = fake_user(id=uuid4(), token_hash=token_hash, is_revoked=False)
        refresh_repo.get_by_hash.return_value = stored
        user_repo.get_by_id.return_value = fake_user()
        tenant_repo.get_by_id.return_value = fake_user(is_active=True)

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        new_access, new_refresh = service.refresh(old_token)

        refresh_repo.update.assert_called_with(stored.id, {"is_revoked": True})
        assert isinstance(new_access, str)
        assert isinstance(new_refresh, str)

    def test_refresh_revoked_token_raises(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.jwt import create_refresh_token

        token = create_refresh_token(USER_ID)
        from hashlib import sha256

        token_hash = sha256(token.encode()).hexdigest()
        refresh_repo.get_by_hash.return_value = fake_user(
            token_hash=token_hash, is_revoked=True
        )

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        with pytest.raises(UnauthorizedError, match="revoked"):
            service.refresh(token)


class TestAuthServiceLogout:
    def test_logout_revokes_token(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)

        from app.auth.jwt import create_refresh_token

        token = create_refresh_token(USER_ID)
        from hashlib import sha256

        token_hash = sha256(token.encode()).hexdigest()
        stored = fake_user(id=uuid4(), token_hash=token_hash, is_revoked=False)
        refresh_repo.get_by_hash.return_value = stored

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        service.logout(token)

        refresh_repo.update.assert_called_with(stored.id, {"is_revoked": True})

    def test_logout_unknown_token_does_nothing(self) -> None:
        user_repo = mock_repo(UserRepository)
        tenant_repo = mock_repo(TenantRepository)
        refresh_repo = mock_repo(RefreshTokenRepository)
        refresh_repo.get_by_hash.return_value = None

        service = AuthService(user_repo, tenant_repo, refresh_repo)
        service.logout("some-invalid-token")

        refresh_repo.update.assert_not_called()
