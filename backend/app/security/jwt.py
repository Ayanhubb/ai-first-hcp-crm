"""JWT access-token create and decode helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from app.core.config import Settings, get_settings
from app.security.utils import generate_jti


class TokenError(Exception):
    """Base error for JWT failures."""


class TokenExpiredError(TokenError):
    """Access token has expired."""


class TokenInvalidError(TokenError):
    """Access token is malformed, tampered, or otherwise invalid."""


def create_access_token(
    *,
    subject: UUID | str,
    role: str,
    email: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> str:
    """
    Mint a signed access JWT.

    Claims: ``sub``, ``role``, ``email``, ``jti``, ``iat``, ``exp``.
    """
    cfg = settings or get_settings()
    now = datetime.now(UTC)
    ttl = expires_delta if expires_delta is not None else timedelta(seconds=cfg.JWT_ACCESS_TTL)
    subject_str = str(subject)

    payload: dict[str, Any] = {
        "sub": subject_str,
        "role": role,
        "email": email,
        "jti": generate_jti(),
        "iat": now,
        "exp": now + ttl,
    }
    if extra_claims:
        # Guard reserved claims from accidental overwrite.
        reserved = {"sub", "role", "email", "jti", "iat", "exp"}
        payload.update({k: v for k, v in extra_claims.items() if k not in reserved})

    return jwt.encode(payload, cfg.JWT_SECRET, algorithm=cfg.JWT_ALGORITHM)


def decode_access_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Decode and validate an access JWT.

    Raises:
        TokenExpiredError: when ``exp`` is in the past.
        TokenInvalidError: for any other validation failure.
    """
    cfg = settings or get_settings()
    if not token or not token.strip():
        raise TokenInvalidError("Access token is empty")

    try:
        payload = jwt.decode(
            token,
            cfg.JWT_SECRET,
            algorithms=[cfg.JWT_ALGORITHM],
            options={
                "require": ["sub", "exp", "iat", "jti", "role", "email"],
            },
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Access token has expired") from exc
    except (InvalidTokenError, PyJWTError) as exc:
        raise TokenInvalidError("Access token is invalid") from exc

    return payload


def get_access_token_expires_in(settings: Settings | None = None) -> int:
    """Return access-token TTL in seconds (for ``expires_in`` response field)."""
    cfg = settings or get_settings()
    return int(cfg.JWT_ACCESS_TTL)
