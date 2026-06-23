from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.jwt import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.password import hash_password, verify_password
from app.core.exceptions import ConflictError, UnauthorizedError
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.tenant import TenantRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest
from app.schemas.tenant import TenantCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.tenant_repo = TenantRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    def register(self, data: RegisterRequest) -> tuple[str, str, dict]:
        if self.user_repo.get_by_email(data.email):
            raise ConflictError("Email already registered")

        if self.tenant_repo.get_by_slug(data.company_slug):
            raise ConflictError("Company slug already taken")

        tenant = self.tenant_repo.create(
            TenantCreate(name=data.company_name, slug=data.company_slug)
        )

        user = self.user_repo.create(
            {
                "email": data.email,
                "password_hash": hash_password(data.password),
                "full_name": data.full_name,
            },
            tenant_id=tenant.id,
        )

        access = create_access_token(user.id, tenant.id, user.role)
        refresh = create_refresh_token(user.id)

        self._store_refresh_token(user.id, refresh)

        user_data = {
            "id": str(user.id),
            "tenant_id": str(tenant.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
        return access, refresh, user_data

    def login(self, email: str, password: str) -> tuple[str, str, dict]:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("User is inactive")

        tenant = self.tenant_repo.get_by_id(user.tenant_id)
        if not tenant or not tenant.is_active:
            raise UnauthorizedError("Tenant is inactive")

        access = create_access_token(user.id, tenant.id, user.role)
        refresh = create_refresh_token(user.id)

        self._store_refresh_token(user.id, refresh)

        user_data = {
            "id": str(user.id),
            "tenant_id": str(tenant.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
        return access, refresh, user_data

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != TokenType.REFRESH:
            raise UnauthorizedError("Invalid refresh token")

        token_hash = self._hash_token(refresh_token)
        stored = self.refresh_repo.get_by_hash(token_hash)
        if not stored or stored.is_revoked:
            raise UnauthorizedError("Refresh token revoked or not found")

        stored.is_revoked = True
        self.db.flush()

        user = self.user_repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        tenant = self.tenant_repo.get_by_id(user.tenant_id)
        if not tenant or not tenant.is_active:
            raise UnauthorizedError("Tenant is inactive")

        new_access = create_access_token(user.id, tenant.id, user.role)
        new_refresh = create_refresh_token(user.id)

        self._store_refresh_token(user.id, new_refresh)

        return new_access, new_refresh

    def logout(self, refresh_token: str) -> None:
        token_hash = self._hash_token(refresh_token)
        stored = self.refresh_repo.get_by_hash(token_hash)
        if stored:
            stored.is_revoked = True
            self.db.flush()

    def _store_refresh_token(self, user_id: UUID, token: str) -> None:
        from hashlib import sha256

        token_hash = sha256(token.encode()).hexdigest()
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)

        entity = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=exp,
        )
        self.db.add(entity)
        self.db.flush()

    @staticmethod
    def _hash_token(token: str) -> str:
        from hashlib import sha256

        return sha256(token.encode()).hexdigest()
