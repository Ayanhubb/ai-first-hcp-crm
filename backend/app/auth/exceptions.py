"""Auth-layer exception aliases mapped to core AppError hierarchy."""

from __future__ import annotations

from app.core.constants import ErrorCode
from app.core.exceptions import ForbiddenError as _ForbiddenError
from app.core.exceptions import UnauthorizedError as _UnauthorizedError


class AuthError(Exception):
    """Marker for auth-package specific errors (prefer core AppError subclasses)."""


class UnauthorizedError(_UnauthorizedError):
    """401 — authentication required / failed."""


class InvalidCredentialsError(UnauthorizedError):
    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message, code=ErrorCode.INVALID_CREDENTIALS)


class TokenInvalidError(UnauthorizedError):
    def __init__(self, message: str = "Token is invalid") -> None:
        super().__init__(message, code=ErrorCode.TOKEN_INVALID)


class TokenExpiredError(UnauthorizedError):
    def __init__(self, message: str = "Token has expired") -> None:
        super().__init__(message, code=ErrorCode.TOKEN_INVALID)


class TokenRevokedError(UnauthorizedError):
    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message, code=ErrorCode.TOKEN_REVOKED)


class ForbiddenError(_ForbiddenError):
    """403 — authenticated but not permitted."""


class UserInactiveError(ForbiddenError):
    def __init__(self, message: str = "User account is inactive") -> None:
        super().__init__(message, code=ErrorCode.USER_INACTIVE)
