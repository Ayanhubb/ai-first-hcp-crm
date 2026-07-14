"""Dashboard KPI schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ORMModel
from app.schemas.enums import FollowUpPriority, InteractionSentiment


class RecentInteractionItem(ORMModel):
    id: UUID
    hcp_name: str
    visit_at: datetime
    sentiment: InteractionSentiment | None = None


class PendingFollowUpItem(ORMModel):
    id: UUID
    title: str
    due_at: datetime | None = None
    priority: FollowUpPriority


class DashboardSummaryResponse(ORMModel):
    interactions_this_week: int
    open_follow_ups: int
    recent_interactions: list[RecentInteractionItem]
    pending_follow_ups: list[PendingFollowUpItem]
