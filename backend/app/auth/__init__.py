"""Authentication & authorization package (JWT principal + RBAC dependencies)."""

from app.auth.dependencies import (
    RequireAdmin,
    RequireAnyRole,
    RequireAuthenticated,
    RequireMR,
    get_access_token_payload,
    get_bearer_credentials,
    get_current_user,
    require_roles,
)
from app.auth.exceptions import (
    AuthError,
    ForbiddenError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    UnauthorizedError,
    UserInactiveError,
)
from app.auth.principals import AccessTokenPayload, AuthenticatedUser, TokenPair
from app.auth.roles import ALL_ROLES, UserRole, normalize_role, role_allowed
from app.auth.tokens import issue_token_pair

__all__ = [
    "ALL_ROLES",
    "AccessTokenPayload",
    "AuthError",
    "AuthenticatedUser",
    "ForbiddenError",
    "InvalidCredentialsError",
    "RequireAdmin",
    "RequireAnyRole",
    "RequireAuthenticated",
    "RequireMR",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenPair",
    "TokenRevokedError",
    "UnauthorizedError",
    "UserInactiveError",
    "UserRole",
    "get_access_token_payload",
    "get_bearer_credentials",
    "get_current_user",
    "issue_token_pair",
    "normalize_role",
    "require_roles",
    "role_allowed",
]
