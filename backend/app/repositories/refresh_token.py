from uuid import UUID

from sqlalchemy import select, update

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db):
        super().__init__(RefreshToken, db)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).scalar_one_or_none()

    def revoke(self, token_id: UUID) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(is_revoked=True)
        )
        self.db.flush()

    def revoke_all_for_user(self, user_id: UUID) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                ~RefreshToken.is_revoked,
            )
            .values(is_revoked=True)
        )
        self.db.flush()
