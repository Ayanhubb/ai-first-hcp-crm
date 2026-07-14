"""Credential verification and JWT / refresh-token lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.exceptions import (
    InvalidCredentialsError,
    TokenInvalidError,
    TokenRevokedError,
    UserInactiveError,
)
from app.auth.tokens import issue_token_pair
from app.core.config import Settings, get_settings
from app.repositories.audit_repository import AuditRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, TokenResponse
from app.schemas.user import UserResponse
from app.security.passwords import needs_rehash, verify_password
from app.security.refresh import hash_refresh_token


class AuthService:
    """Authenticate users and manage access / refresh token pairs."""

    def __init__(
        self,
        session: Session,
        *,
        user_repo: UserRepository | None = None,
        refresh_repo: RefreshTokenRepository | None = None,
        audit_repo: AuditRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._users = user_repo or UserRepository(session)
        self._refresh = refresh_repo or RefreshTokenRepository(session)
        self._audits = audit_repo or AuditRepository(session)
        self._settings = settings or get_settings()

    def login(
        self,
        *,
        email: str,
        password: str,
        correlation_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        user = self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            self._audit_login_failed(email=email, correlation_id=correlation_id, ip_address=ip_address)
            self._session.commit()
            raise InvalidCredentialsError()

        if not user.is_active:
            self._audits.append(
                actor_user_id=user.id,
                entity_type="user",
                entity_id=user.id,
                action="LOGIN_FAILED",
                correlation_id=correlation_id,
                after_state={"reason": "inactive"},
                ip_address=ip_address,
            )
            self._session.commit()
            raise UserInactiveError()

        if needs_rehash(user.password_hash):
            # Soft signal only; password upgrade happens on next intentional change.
            pass

        pair, refresh_hash, expires_at = issue_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            settings=self._settings,
        )
        self._refresh.create(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._audits.append(
            actor_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            action="LOGIN",
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        self._session.commit()

        return LoginResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
            user=UserResponse.model_validate(user),
        )

    def refresh(
        self,
        *,
        refresh_token: str,
        correlation_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        token_hash = hash_refresh_token(refresh_token)
        stored = self._refresh.get_by_hash(token_hash)
        if stored is None:
            raise TokenInvalidError()

        now = datetime.now(UTC)
        if stored.revoked_at is not None:
            raise TokenRevokedError()
        if stored.expires_at <= now:
            self._refresh.revoke(stored, revoked_at=now)
            self._session.commit()
            raise TokenInvalidError("Refresh token has expired")

        user = self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            self._refresh.revoke(stored, revoked_at=now)
            self._session.commit()
            raise TokenInvalidError()

        self._refresh.revoke(stored, revoked_at=now)
        pair, new_hash, expires_at = issue_token_pair(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            settings=self._settings,
        )
        self._refresh.create(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._audits.append(
            actor_user_id=user.id,
            entity_type="user",
            entity_id=user.id,
            action="TOKEN_REFRESH",
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        self._session.commit()

        return TokenResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
            user=UserResponse.model_validate(user),
        )

    def logout(
        self,
        *,
        refresh_token: str,
        actor_user_id: UUID | None,
        correlation_id: UUID,
        ip_address: str | None = None,
    ) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored = self._refresh.get_by_hash(token_hash)
        if stored is not None and stored.revoked_at is None:
            self._refresh.revoke(stored)
            entity_id = stored.user_id
            actor = actor_user_id or stored.user_id
            self._audits.append(
                actor_user_id=actor,
                entity_type="user",
                entity_id=entity_id,
                action="LOGOUT",
                correlation_id=correlation_id,
                ip_address=ip_address,
            )
            self._session.commit()
        # Idempotent: missing / already-revoked tokens succeed silently.

    def _audit_login_failed(
        self,
        *,
        email: str,
        correlation_id: UUID,
        ip_address: str | None,
    ) -> None:
        # entity_id requires a UUID; use nil UUID when email is unknown.
        self._audits.append(
            actor_user_id=None,
            entity_type="user",
            entity_id=UUID(int=0),
            action="LOGIN_FAILED",
            correlation_id=correlation_id,
            after_state={"email": email.lower()},
            ip_address=ip_address,
        )
