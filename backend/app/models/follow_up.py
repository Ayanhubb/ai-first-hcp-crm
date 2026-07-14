"""Follow-up next-action ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import FollowUpPriority, FollowUpStatus, RecordSource

if TYPE_CHECKING:
    from app.models.interaction import Interaction
    from app.models.user import User


class FollowUp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "follow_ups"
    __table_args__ = (
        CheckConstraint(
            "length(trim(title)) > 0",
            name="ck_follow_ups_title_nonempty",
        ),
        Index("ix_follow_ups_user_status_due", "user_id", "status", "due_at"),
        Index("ix_follow_ups_interaction_id", "interaction_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "interactions.id",
            name="fk_follow_ups_interactions",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_follow_ups_users", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[FollowUpPriority] = mapped_column(
        Enum(
            FollowUpPriority,
            name="follow_up_priority",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'medium'::follow_up_priority"),
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(
            FollowUpStatus,
            name="follow_up_status",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'open'::follow_up_status"),
    )
    source: Mapped[RecordSource] = mapped_column(
        Enum(
            RecordSource,
            name="record_source",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'manual'::record_source"),
    )

    interaction: Mapped[Interaction] = relationship(back_populates="follow_ups")
    user: Mapped[User] = relationship(
        back_populates="follow_ups",
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        return f"<FollowUp id={self.id!s} title={self.title!r}>"
