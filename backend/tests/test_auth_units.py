"""Auth module unit tests — JWT, password hashing, permissions.

These tests have zero dependencies on DB or FastAPI (pure functions).
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.auth.jwt import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.password import hash_password, verify_password
from app.auth.permissions import has_permission
from app.core.constants import Permission, Role

USER_ID = uuid4()
TENANT_ID = uuid4()


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    def test_payload_contains_expected_fields(self) -> None:
        token = create_access_token(USER_ID, TENANT_ID, Role.ADMIN)
        payload = decode_token(token)

        assert payload["sub"] == str(USER_ID)
        assert payload["tenant_id"] == str(TENANT_ID)
        assert payload["role"] == Role.ADMIN
        assert payload["type"] == TokenType.ACCESS
        assert "exp" in payload
        assert "iat" in payload

    def test_expiration_is_future(self) -> None:
        token = create_access_token(USER_ID, TENANT_ID, Role.ADMIN)
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp > datetime.now(UTC)

    def test_different_user_different_token(self) -> None:
        uid_a, uid_b = uuid4(), uuid4()
        token_a = create_access_token(uid_a, TENANT_ID, Role.ADMIN)
        token_b = create_access_token(uid_b, TENANT_ID, Role.ADMIN)
        assert token_a != token_b


class TestCreateRefreshToken:
    def test_payload_contains_jti_and_type(self) -> None:
        token = create_refresh_token(USER_ID)
        payload = decode_token(token)

        assert payload["sub"] == str(USER_ID)
        assert payload["type"] == TokenType.REFRESH
        assert "jti" in payload

    def test_has_no_tenant_id(self) -> None:
        token = create_refresh_token(USER_ID)
        payload = decode_token(token)
        assert "tenant_id" not in payload


class TestDecodeToken:
    def test_decode_valid_token_returns_payload(self) -> None:
        token = create_access_token(USER_ID, TENANT_ID, Role.ADMIN)
        payload = decode_token(token)
        assert payload["sub"] == str(USER_ID)

    def test_decode_garbage_returns_empty_dict(self) -> None:
        assert decode_token("not.a.token") == {}

    def test_decode_empty_string_returns_empty_dict(self) -> None:
        assert decode_token("") == {}

    def test_decode_expired_token_returns_empty_dict(self) -> None:
        from app.core.config import settings
        from jose import jwt

        payload = {
            "sub": str(USER_ID),
            "type": TokenType.ACCESS,
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        expired = jwt.encode(
            payload, settings.secret_key, algorithm=settings.algorithm
        )
        assert decode_token(expired) == {}

    def test_decode_tampered_token_returns_empty_dict(self) -> None:
        token = create_access_token(USER_ID, TENANT_ID, Role.ADMIN)
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) == {}


# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------


class TestHashPassword:
    def test_hash_is_string(self) -> None:
        h = hash_password("hello")
        assert isinstance(h, str)
        assert len(h) > 20

    def test_same_password_different_hashes(self) -> None:
        h1 = hash_password("hello")
        h2 = hash_password("hello")
        assert h1 != h2  # bcrypt uses random salt


class TestVerifyPassword:
    def test_correct_password(self) -> None:
        h = hash_password("my-password")
        assert verify_password("my-password", h) is True

    def test_wrong_password(self) -> None:
        h = hash_password("my-password")
        assert verify_password("wrong", h) is False

    def test_empty_password(self) -> None:
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("x", h) is False


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class TestHasPermission:
    @pytest.mark.parametrize(
        "role,permission,expected",
        [
            (Role.SUPER_ADMIN, Permission.PROJECT_CREATE, True),
            (Role.SUPER_ADMIN, Permission.CLIENT_DELETE, True),
            (Role.ADMIN, Permission.PROJECT_CREATE, True),
            (Role.ADMIN, Permission.USER_CREATE, True),
            (Role.PROJECT_MANAGER, Permission.PROJECT_UPDATE, True),
            (Role.PROJECT_MANAGER, Permission.CLIENT_READ, True),
            (Role.PROJECT_MANAGER, Permission.CLIENT_CREATE, False),
            (Role.PROJECT_MANAGER, Permission.USER_CREATE, False),
            (Role.WORKER, Permission.PROJECT_READ, True),
            (Role.WORKER, Permission.DAILY_REPORT_CREATE, True),
            (Role.WORKER, Permission.PROJECT_CREATE, False),
            (Role.WORKER, Permission.CLIENT_READ, False),
            (Role.CLIENT_VIEWER, Permission.REPORT_READ, True),
            (Role.CLIENT_VIEWER, Permission.REPORT_DOWNLOAD, True),
            (Role.CLIENT_VIEWER, Permission.PROJECT_CREATE, False),
        ],
    )
    def test_permission_matrix(
        self,
        role: Role,
        permission: Permission,
        expected: bool,
    ) -> None:
        from types import SimpleNamespace

        user = SimpleNamespace(role=role)
        assert has_permission(user, permission) is expected
