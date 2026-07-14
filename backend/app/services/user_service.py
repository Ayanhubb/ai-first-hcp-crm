"""User profile and admin directory use cases."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.enums import UserRole as OrmUserRole
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page, PaginationParams, parse_sort
from app.schemas.enums import UserRole
from app.schemas.user import UserResponse


_USER_SORT = frozenset({"created_at", "email", "full_name"})


class UserService:
    """Profile and admin listing for ``users``."""

    def __init__(self, session: Session, user_repo: UserRepository | None = None) -> None:
        self._session = session
        self._users = user_repo or UserRepository(session)

    def get_me(self, user_id: uuid.UUID) -> UserResponse:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)

    def list_users(
        self,
        *,
        pagination: PaginationParams,
        role: UserRole | None = None,
        is_active: bool | None = None,
        query: str | None = None,
        sort: str | None = None,
    ) -> Page[UserResponse]:
        try:
            sort_spec = parse_sort(sort, whitelist=_USER_SORT, default="created_at:desc")
        except ValueError as exc:
            raise ValidationAppError(str(exc), details=[{"field": "sort", "issue": str(exc)}]) from exc

        orm_role = OrmUserRole(role.value) if role is not None else None
        rows, total = self._users.list_admin(
            page=pagination.page,
            page_size=pagination.page_size,
            sort=sort_spec,
            role=orm_role,
            is_active=is_active,
            query=query,
        )
        return Page[UserResponse](
            items=[UserResponse.model_validate(row) for row in rows],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
