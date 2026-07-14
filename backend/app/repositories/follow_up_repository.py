"""Follow-up persistence repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import FollowUpStatus
from app.models.follow_up import FollowUp


class FollowUpRepository:
    """Data access for ``follow_ups``."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def bulk_create(self, follow_ups: list[FollowUp]) -> list[FollowUp]:
        for row in follow_ups:
            self._session.add(row)
        self._session.flush()
        return follow_ups

    def list_open_for_user(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[FollowUp]:
        stmt = (
            select(FollowUp)
            .where(
                FollowUp.user_id == user_id,
                FollowUp.status == FollowUpStatus.OPEN,
            )
            .order_by(FollowUp.due_at.asc().nulls_last(), FollowUp.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def count_open_for_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(FollowUp)
            .where(
                FollowUp.user_id == user_id,
                FollowUp.status == FollowUpStatus.OPEN,
            )
        )
        return int(self._session.scalar(stmt) or 0)

    def get_by_id(self, follow_up_id: uuid.UUID) -> FollowUp | None:
        return self._session.get(FollowUp, follow_up_id)

    def update(self, follow_up: FollowUp) -> FollowUp:
        self._session.add(follow_up)
        self._session.flush()
        return follow_up
