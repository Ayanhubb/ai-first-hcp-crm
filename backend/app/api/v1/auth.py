"""Authentication APIs — login, refresh, logout."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import get_auth_service
from app.auth.principals import AuthenticatedUser
from app.core.config import Settings, get_settings
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, RefreshRequest, TokenResponse
from app.security.jwt import TokenExpiredError as JwtExpiredError
from app.security.jwt import TokenInvalidError as JwtInvalidError
from app.security.jwt import decode_access_token
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
_optional_bearer = HTTPBearer(auto_error=False)


def _correlation_uuid(request: Request) -> UUID:
    raw = getattr(request.state, "correlation_id", None)
    try:
        return UUID(str(raw)) if raw else UUID(int=0)
    except ValueError:
        return UUID(int=0)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser | None:
    """Bearer recommended but not required for logout."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        return None
    try:
        from app.auth.principals import AccessTokenPayload

        raw = decode_access_token(credentials.credentials, settings=settings)
        return AuthenticatedUser.from_payload(AccessTokenPayload.from_decoded(raw))
    except (JwtExpiredError, JwtInvalidError, KeyError, ValueError, TypeError):
        return None


@router.post("/login", response_model=LoginResponse, summary="Login")
def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return service.login(
        email=str(payload.email),
        password=payload.password,
        correlation_id=_correlation_uuid(request),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh tokens")
def refresh(
    payload: RefreshRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return service.refresh(
        refresh_token=payload.refresh_token,
        correlation_id=_correlation_uuid(request),
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Logout (revoke refresh token)",
)
def logout(
    payload: LogoutRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[AuthenticatedUser | None, Depends(_optional_user)] = None,
) -> Response:
    actor_id = current_user.id if current_user is not None else None
    service.logout(
        refresh_token=payload.refresh_token,
        actor_user_id=actor_id,
        correlation_id=_correlation_uuid(request),
        ip_address=_client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
