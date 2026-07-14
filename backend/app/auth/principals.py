"""Authenticated principal and JWT payload models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.roles import UserRole, normalize_role


class AccessTokenPayload(BaseModel):
    """Validated JWT access-token claims."""

    model_config = ConfigDict(extra="ignore")

    sub: UUID
    role: UserRole
    email: EmailStr
    jti: str
    iat: int | float
    exp: int | float

    @classmethod
    def from_decoded(cls, payload: dict[str, Any]) -> AccessTokenPayload:
        """Build from a raw ``jwt.decode`` dict."""
        return cls.model_validate(
            {
                "sub": payload["sub"],
                "role": normalize_role(payload["role"]),
                "email": payload["email"],
                "jti": payload["jti"],
                "iat": payload["iat"],
                "exp": payload["exp"],
            }
        )


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """
    Lightweight auth principal derived from a valid access token.

    Used by FastAPI dependencies for RBAC without coupling to ORM models.
    Services may later resolve the full ``User`` aggregate by ``id``.
    """

    id: UUID
    email: str
    role: UserRole
    jti: str
    token_payload: AccessTokenPayload

    @classmethod
    def from_payload(cls, payload: AccessTokenPayload) -> AuthenticatedUser:
        return cls(
            id=payload.sub,
            email=str(payload.email),
            role=payload.role,
            jti=payload.jti,
            token_payload=payload,
        )

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN

    def has_role(self, *roles: str | UserRole) -> bool:
        from app.auth.roles import role_allowed

        return role_allowed(self.role, *roles)


class TokenPair(BaseModel):
    """Access + refresh issuance result (service/router boundary)."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)
