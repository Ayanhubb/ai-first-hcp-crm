"""Refresh-token persistence repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.auth_refresh_token import AuthRefreshToken


class RefreshTokenRepository:
    """Data access for ``auth_refresh_tokens`` (hashes only)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> AuthRefreshToken:
        row = AuthRefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_by_hash(self, token_hash: str) -> AuthRefreshToken | None:
        stmt = select(AuthRefreshToken).where(AuthRefreshToken.token_hash == token_hash)
        return self._session.scalars(stmt).first()

    def revoke(
        self,
        token: AuthRefreshToken,
        *,
        revoked_at: datetime | None = None,
    ) -> AuthRefreshToken:
        token.revoked_at = revoked_at or datetime.now(UTC)
        self._session.add(token)
        self._session.flush()
        return token

    def revoke_all_for_user(self, user_id: uuid.UUID, *, revoked_at: datetime) -> int:
        stmt = (
            update(AuthRefreshToken)
            .where(
                AuthRefreshToken.user_id == user_id,
                AuthRefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        result = self._session.execute(stmt)
        self._session.flush()
        return int(result.rowcount or 0)
