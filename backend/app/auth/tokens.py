"""Convenience helpers for issuing token pairs (used by AuthService later)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.auth.principals import TokenPair
from app.auth.roles import UserRole, normalize_role
from app.core.config import Settings, get_settings
from app.security.jwt import create_access_token, get_access_token_expires_in
from app.security.refresh import (
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expires_at,
)


def issue_token_pair(
    *,
    user_id: UUID | str,
    email: str,
    role: str | UserRole,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[TokenPair, str, datetime]:
    """
    Issue an access JWT plus opaque refresh token.

    Returns:
        ``(token_pair, refresh_token_hash, refresh_expires_at)``

    The plaintext refresh token is only inside ``TokenPair.refresh_token``.
    Persist ``refresh_token_hash`` (never the plaintext) in ``auth_refresh_tokens``.
    """
    cfg = settings or get_settings()
    normalized_role = normalize_role(role)

    access_token = create_access_token(
        subject=user_id,
        role=normalized_role.value,
        email=email,
        extra_claims=extra_claims,
        settings=cfg,
    )
    raw_refresh = generate_refresh_token()
    refresh_hash = hash_refresh_token(raw_refresh)
    expires_at = refresh_token_expires_at(settings=cfg)

    pair = TokenPair(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=get_access_token_expires_in(cfg),
    )
    return pair, refresh_hash, expires_at
