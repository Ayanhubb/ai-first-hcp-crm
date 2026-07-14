"""Dashboard KPI aggregation use cases."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.follow_up_repository import FollowUpRepository
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PendingFollowUpItem,
    RecentInteractionItem,
)
from app.schemas.enums import FollowUpPriority, InteractionSentiment


class DashboardService:
    """Aggregate MR home KPIs scoped to the authenticated user."""

    def __init__(
        self,
        session: Session,
        interaction_repo: InteractionRepository | None = None,
        follow_up_repo: FollowUpRepository | None = None,
    ) -> None:
        self._session = session
        self._interactions = interaction_repo or InteractionRepository(session)
        self._follow_ups = follow_up_repo or FollowUpRepository(session)

    def get_summary(self, user_id: UUID) -> DashboardSummaryResponse:
        now = datetime.now(UTC)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        interactions_this_week = self._interactions.count_for_user_since(
            user_id=user_id,
            since=week_start,
        )
        open_follow_ups = self._follow_ups.count_open_for_user(user_id)
        recent_rows = self._interactions.list_recent_for_user(user_id=user_id, limit=5)
        pending = self._follow_ups.list_open_for_user(user_id=user_id, limit=10)

        return DashboardSummaryResponse(
            interactions_this_week=interactions_this_week,
            open_follow_ups=open_follow_ups,
            recent_interactions=[
                RecentInteractionItem(
                    id=ix.id,
                    hcp_name=f"{hcp.first_name} {hcp.last_name}".strip(),
                    visit_at=ix.visit_at,
                    sentiment=(
                        InteractionSentiment(ix.sentiment.value)
                        if ix.sentiment is not None
                        else None
                    ),
                )
                for ix, hcp in recent_rows
            ],
            pending_follow_ups=[
                PendingFollowUpItem(
                    id=fu.id,
                    title=fu.title,
                    due_at=fu.due_at,
                    priority=FollowUpPriority(fu.priority.value),
                )
                for fu in pending
            ],
        )
