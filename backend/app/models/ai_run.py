"""LangGraph AI run provenance ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AiRunStatus

if TYPE_CHECKING:
    from app.models.hcp import HealthcareProfessional
    from app.models.interaction import Interaction
    from app.models.user import User


class AiRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_runs"
    __table_args__ = (
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_ai_runs_latency_nonneg",
        ),
        Index("ix_ai_runs_user_created", "user_id", text("created_at DESC")),
        Index("ix_ai_runs_hcp_created", "hcp_id", text("created_at DESC")),
        Index("ix_ai_runs_status", "status"),
        Index("ix_ai_runs_interaction_id", "interaction_id"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_ai_runs_users", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    hcp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "healthcare_professionals.id",
            name="fk_ai_runs_hcps",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "interactions.id",
            name="fk_ai_runs_interactions",
            onupdate="CASCADE",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
    )
    graph_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[AiRunStatus] = mapped_column(
        Enum(
            AiRunStatus,
            name="ai_run_status",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'running'::ai_run_status"),
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User | None] = relationship(
        back_populates="ai_runs",
        foreign_keys=[user_id],
    )
    hcp: Mapped[HealthcareProfessional | None] = relationship(
        back_populates="ai_runs",
        foreign_keys=[hcp_id],
    )
    interaction: Mapped[Interaction | None] = relationship(
        back_populates="draft_ai_runs",
        foreign_keys=[interaction_id],
    )
    saved_interactions: Mapped[list[Interaction]] = relationship(
        back_populates="ai_run",
        foreign_keys="Interaction.ai_run_id",
    )

    def __repr__(self) -> str:
        return f"<AiRun id={self.id!s} status={self.status!s}>"
