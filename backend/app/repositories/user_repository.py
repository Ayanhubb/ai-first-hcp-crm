"""User persistence repository."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import SortSpec


class UserRepository:
    """Data access for the ``users`` table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.strip().lower())
        return self._session.scalars(stmt).first()

    def list_admin(
        self,
        *,
        page: int,
        page_size: int,
        sort: SortSpec,
        role: UserRole | None = None,
        is_active: bool | None = None,
        query: str | None = None,
    ) -> tuple[list[User], int]:
        filters: list[object] = []
        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active.is_(is_active))
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(
                or_(
                    User.email.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(User)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int(self._session.scalar(count_stmt) or 0)

        order_col = {
            "created_at": User.created_at,
            "email": User.email,
            "full_name": User.full_name,
        }[sort.field]
        order_by = order_col.desc() if sort.is_desc else order_col.asc()

        stmt: Select[tuple[User]] = select(User)
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._session.scalars(stmt).all()), total
