"""Users API — profile and admin directory."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import RequireAdmin, RequireAnyRole, get_user_service
from app.schemas.common import Page, PaginationParams
from app.schemas.enums import UserRole
from app.schemas.user import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get current user")
def get_me(
    current_user: RequireAnyRole,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    return service.get_me(current_user.id)


@router.get("", response_model=Page[UserResponse], summary="List users (admin)")
def list_users(
    _admin: RequireAdmin,
    service: Annotated[UserService, Depends(get_user_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    role: UserRole | None = None,
    is_active: bool | None = None,
    query: str | None = Query(None, min_length=1, max_length=200),
    sort: str | None = None,
) -> Page[UserResponse]:
    return service.list_users(
        pagination=PaginationParams(page=page, page_size=page_size),
        role=role,
        is_active=is_active,
        query=query,
        sort=sort,
    )
