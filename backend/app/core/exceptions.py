"""Application exceptions and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.constants import REQUEST_ID_HEADER, ErrorCode
from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Base application error mapped to an HTTP error envelope."""

    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []
        self.headers = headers or {}


class ValidationAppError(AppError):
    def __init__(
        self,
        message: str = "Validation failed",
        *,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        code: str = ErrorCode.UNAUTHORIZED,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(AppError):
    def __init__(
        self,
        message: str = "Forbidden",
        *,
        code: str = ErrorCode.FORBIDDEN,
    ) -> None:
        super().__init__(message, code=code, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(
            message,
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(
            message,
            code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
    ) -> None:
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        super().__init__(
            message,
            code=ErrorCode.RATE_LIMITED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
        )


class AiProviderError(AppError):
    def __init__(self, message: str = "AI provider error") -> None:
        super().__init__(
            message,
            code=ErrorCode.AI_PROVIDER_ERROR,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class AiTimeoutError(AppError):
    def __init__(self, message: str = "AI request timed out") -> None:
        super().__init__(
            message,
            code=ErrorCode.AI_TIMEOUT,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


def _correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None) or request.headers.get(
        REQUEST_ID_HEADER
    )


def error_envelope(
    *,
    code: str,
    message: str,
    correlation_id: str | None,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "correlation_id": correlation_id,
        }
    }


def _json_error(
    *,
    status_code: int,
    code: str,
    message: str,
    correlation_id: str | None,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_envelope(
            code=code,
            message=message,
            correlation_id=correlation_id,
            details=details,
        ),
        headers=headers,
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for error in exc.errors():
        location = error.get("loc", ())
        field = ".".join(str(part) for part in location if part != "body")
        details.append(
            {
                "field": field or None,
                "issue": error.get("msg", "invalid"),
            }
        )
    return details


def register_exception_handlers(app: FastAPI) -> None:
    """Attach standardized exception handlers to the FastAPI app."""

    # Auth package exceptions (do not modify app.auth — map here for HTTP envelope).
    from app.auth.exceptions import AuthError

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        correlation_id = _correlation_id(request)
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return _json_error(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
            headers=headers,
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.warning(
            "app_error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            correlation_id=correlation_id,
        )
        return _json_error(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            correlation_id=correlation_id,
            details=exc.details,
            headers=exc.headers or None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        correlation_id = _correlation_id(request)
        return _json_error(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed",
            correlation_id=correlation_id,
            details=_validation_details(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        correlation_id = _correlation_id(request)
        code_map = {
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            429: ErrorCode.RATE_LIMITED,
        }
        code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _json_error(
            status_code=exc.status_code,
            code=code,
            message=message,
            correlation_id=correlation_id,
            headers=dict(exc.headers) if exc.headers else None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = _correlation_id(request)
        logger.exception(
            "unhandled_exception",
            error=str(exc),
            correlation_id=correlation_id,
        )
        return _json_error(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            correlation_id=correlation_id,
        )
