"""User request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import ORMModel, Page
from app.schemas.enums import UserRole


class UserResponse(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserMeResponse(UserResponse):
    """Authenticated profile (`GET /users/me`)."""


class UserListParams(ORMModel):
    """Admin user directory filters."""

    role: UserRole | None = None
    is_active: bool | None = None
    query: str | None = Field(default=None, min_length=1, max_length=200)
    sort: str | None = None


UserPage = Page[UserResponse]
