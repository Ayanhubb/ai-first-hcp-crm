"""Follow-up status helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.enums import FollowUpStatus
from app.repositories.follow_up_repository import FollowUpRepository
from app.schemas.interaction import FollowUpResponse


class FollowUpService:
    """Basic follow-up status updates."""

    def __init__(
        self,
        session: Session,
        follow_up_repo: FollowUpRepository | None = None,
    ) -> None:
        self._session = session
        self._follow_ups = follow_up_repo or FollowUpRepository(session)

    def set_status(self, follow_up_id: uuid.UUID, status: FollowUpStatus) -> FollowUpResponse:
        row = self._follow_ups.get_by_id(follow_up_id)
        if row is None:
            raise NotFoundError("Follow-up not found")
        row.status = status
        self._follow_ups.update(row)
        self._session.commit()
        return FollowUpResponse.model_validate(row)
