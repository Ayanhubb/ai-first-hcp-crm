"""RBAC roles for the HCP CRM."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """Mirrors PostgreSQL ``user_role`` enum."""

    MR = "mr"
    ADMIN = "admin"


ALL_ROLES: frozenset[UserRole] = frozenset({UserRole.MR, UserRole.ADMIN})


def normalize_role(role: str | UserRole) -> UserRole:
    """Parse a role string into ``UserRole``."""
    if isinstance(role, UserRole):
        return role
    try:
        return UserRole(str(role).strip().lower())
    except ValueError as exc:
        raise ValueError(f"Unknown role: {role!r}") from exc


def role_allowed(user_role: str | UserRole, *allowed: str | UserRole) -> bool:
    """Return True when ``user_role`` is in the allowed set."""
    if not allowed:
        return False
    current = normalize_role(user_role)
    permitted = {normalize_role(r) for r in allowed}
    return current in permitted
