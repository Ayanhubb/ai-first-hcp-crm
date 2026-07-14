"""FastAPI authentication and RBAC dependencies."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.exceptions import ForbiddenError, TokenExpiredError, TokenInvalidError, UnauthorizedError
from app.auth.principals import AccessTokenPayload, AuthenticatedUser
from app.auth.roles import UserRole, normalize_role, role_allowed
from app.core.config import Settings, get_settings
from app.security.jwt import (
    TokenExpiredError as JwtExpiredError,
)
from app.security.jwt import (
    TokenInvalidError as JwtInvalidError,
)
from app.security.jwt import (
    decode_access_token,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_bearer_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    """Require a Bearer credential; raise 401 when missing."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise UnauthorizedError("Missing or invalid Authorization Bearer token")
    return credentials


def get_access_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_bearer_credentials)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AccessTokenPayload:
    """Decode and validate the Bearer access JWT into a typed payload."""
    try:
        raw = decode_access_token(credentials.credentials, settings=settings)
        return AccessTokenPayload.from_decoded(raw)
    except JwtExpiredError as exc:
        raise TokenExpiredError() from exc
    except JwtInvalidError as exc:
        raise TokenInvalidError() from exc
    except (KeyError, ValueError, TypeError) as exc:
        raise TokenInvalidError("Token claims are invalid") from exc


def get_current_user(
    payload: Annotated[AccessTokenPayload, Depends(get_access_token_payload)],
) -> AuthenticatedUser:
    """
    Return the authenticated principal from a valid access token.

    Inactive-user enforcement belongs at login / refresh (AuthService) and any
    optional DB-backed dependency stacked by the API layer later.
    """
    return AuthenticatedUser.from_payload(payload)


def require_roles(*allowed_roles: str | UserRole) -> Callable[..., AuthenticatedUser]:
    """
    FastAPI dependency factory enforcing RBAC against JWT ``role`` claim.

    Usage::

        @router.get("/admin/users")
        def list_users(user: Annotated[AuthenticatedUser, Depends(require_roles("admin"))]):
            ...
    """
    if not allowed_roles:
        raise ValueError("require_roles() requires at least one role")

    normalized = tuple(normalize_role(r) for r in allowed_roles)

    def _dependency(
        user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if not role_allowed(user.role, *normalized):
            raise ForbiddenError(
                f"Requires one of roles: {', '.join(r.value for r in normalized)}"
            )
        return user

    return _dependency


# Common role shortcuts
RequireAdmin = Annotated[AuthenticatedUser, Depends(require_roles(UserRole.ADMIN))]
RequireMR = Annotated[AuthenticatedUser, Depends(require_roles(UserRole.MR))]
RequireAuthenticated = Annotated[AuthenticatedUser, Depends(get_current_user)]
RequireAnyRole = Annotated[
    AuthenticatedUser,
    Depends(require_roles(UserRole.MR, UserRole.ADMIN)),
]
