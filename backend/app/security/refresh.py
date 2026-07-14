"""Opaque refresh-token generation and hashing."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import Settings, get_settings

# High-entropy opaque tokens; 32 bytes → ~43 url-safe characters.
REFRESH_TOKEN_BYTES = 32


def generate_refresh_token(*, nbytes: int = REFRESH_TOKEN_BYTES) -> str:
    """Generate a cryptographically secure opaque refresh token (plaintext)."""
    if nbytes < 32:
        raise ValueError("Refresh tokens must be at least 32 bytes of entropy")
    return secrets.token_urlsafe(nbytes)


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash an opaque refresh token for storage lookups.

    Uses SHA-256 hex digest. Refresh tokens are high-entropy secrets, so a
    fast cryptographic hash is appropriate (unlike password hashing).
    """
    if not raw_token:
        raise ValueError("Refresh token must be non-empty")
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def refresh_token_expires_at(
    *,
    settings: Settings | None = None,
    ttl: timedelta | None = None,
    now: datetime | None = None,
) -> datetime:
    """Compute ``expires_at`` for a newly issued refresh token (UTC-aware)."""
    cfg = settings or get_settings()
    base = now or datetime.now(UTC)
    delta = ttl if ttl is not None else timedelta(seconds=cfg.JWT_REFRESH_TTL)
    return base + delta


def get_refresh_token_ttl(settings: Settings | None = None) -> int:
    """Return refresh-token TTL in seconds."""
    cfg = settings or get_settings()
    return int(cfg.JWT_REFRESH_TTL)
