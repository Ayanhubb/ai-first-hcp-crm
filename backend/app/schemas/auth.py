"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import StrictModel
from app.schemas.user import UserResponse


class LoginRequest(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(StrictModel):
    refresh_token: str = Field(min_length=1, max_length=2048)


class LogoutRequest(StrictModel):
    refresh_token: str = Field(min_length=1, max_length=2048)


class TokenResponse(StrictModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(gt=0)
    user: UserResponse | None = None


class LoginResponse(TokenResponse):
    """Login always includes the authenticated user profile."""

    user: UserResponse
