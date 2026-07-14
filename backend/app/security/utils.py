"""General security utilities."""

from __future__ import annotations

import hmac
import re
import secrets
from typing import Any
from uuid import uuid4

# Patterns used to scrub secrets from log-bound structures.
_SENSITIVE_KEY_RE = re.compile(
    r"(password|passwd|secret|token|authorization|api[_-]?key|refresh)",
    re.IGNORECASE,
)


def generate_jti() -> str:
    """Generate a unique JWT ID (``jti`` claim)."""
    return str(uuid4())


def constant_time_equals(left: str, right: str) -> bool:
    """Constant-time string comparison for secrets."""
    if left is None or right is None:  # type: ignore[comparison-overlap]
        return False
    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))


def generate_secure_secret(nbytes: int = 48) -> str:
    """Generate a url-safe secret suitable for JWT_SECRET rotation demos/ops."""
    if nbytes < 32:
        raise ValueError("Secure secrets should be at least 32 bytes")
    return secrets.token_urlsafe(nbytes)


def redact_secret(value: str | None, *, visible: int = 4) -> str:
    """Redact a secret for safe logging (prefix only)."""
    if not value:
        return "***"
    if len(value) <= visible:
        return "***"
    return f"{value[:visible]}…***"


def scrub_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a shallow copy of ``data`` with sensitive keys redacted.

    Useful before attaching request bodies to structured logs.
    """
    scrubbed: dict[str, Any] = {}
    for key, value in data.items():
        if _SENSITIVE_KEY_RE.search(str(key)):
            scrubbed[key] = redact_secret(str(value) if value is not None else None)
        elif isinstance(value, dict):
            scrubbed[key] = scrub_sensitive(value)
        else:
            scrubbed[key] = value
    return scrubbed


def bearer_token_from_header(authorization: str | None) -> str | None:
    """
    Extract the raw bearer token from an ``Authorization`` header value.

    Returns None when the header is missing or not a Bearer scheme.
    """
    if not authorization:
        return None
    scheme, _, param = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not param:
        return None
    return param.strip() or None
