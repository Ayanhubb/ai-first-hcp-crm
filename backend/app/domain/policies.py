"""Domain policy helpers (pure authorization / invariant checks)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.auth.principals import AuthenticatedUser
from app.auth.roles import UserRole
from app.core.exceptions import ForbiddenError, ValidationAppError
from app.models.interaction import Interaction


def assert_interaction_access(user: AuthenticatedUser, interaction: Interaction) -> None:
    """MR may only access own interactions; admin may access any."""
    if user.role is UserRole.ADMIN:
        return
    if interaction.user_id != user.id:
        raise ForbiddenError("You do not have access to this interaction")


def assert_visit_at_sane(visit_at: datetime, *, max_future: timedelta = timedelta(days=1)) -> None:
    """Reject visit timestamps unreasonably far in the future."""
    now = datetime.now(UTC)
    aware = visit_at if visit_at.tzinfo is not None else visit_at.replace(tzinfo=UTC)
    if aware > now + max_future:
        raise ValidationAppError(
            "visit_at is unreasonably far in the future",
            details=[{"field": "visit_at", "issue": "must be within 1 day from now"}],
        )
