"""Interaction aggregate and discussed-product junction."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    InteractionSentiment,
    InteractionStatus,
    RecordSource,
    VisitChannel,
)

if TYPE_CHECKING:
    from app.models.ai_run import AiRun
    from app.models.follow_up import FollowUp
    from app.models.hcp import HealthcareProfessional
    from app.models.product import Product
    from app.models.user import User


class Interaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interactions"
    __table_args__ = (
        CheckConstraint(
            "sentiment_score IS NULL OR (sentiment_score >= 0 AND sentiment_score <= 1)",
            name="ck_interactions_sentiment_score",
        ),
        CheckConstraint(
            "status <> 'saved' OR length(trim(notes)) > 0",
            name="ck_interactions_notes_nonempty_when_saved",
        ),
        Index("ix_interactions_user_id_visit_at", "user_id", text("visit_at DESC")),
        Index("ix_interactions_hcp_id_visit_at", "hcp_id", text("visit_at DESC")),
        Index(
            "ix_interactions_not_deleted",
            text("visit_at DESC"),
            postgresql_where=text("is_deleted = FALSE"),
        ),
        Index(
            "ix_interactions_status",
            "status",
            postgresql_where=text("is_deleted = FALSE"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_interactions_users", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    hcp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "healthcare_professionals.id",
            name="fk_interactions_hcps",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    visit_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[VisitChannel] = mapped_column(
        Enum(
            VisitChannel,
            name="visit_channel",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[InteractionSentiment | None] = mapped_column(
        Enum(
            InteractionSentiment,
            name="interaction_sentiment",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=True,
    )
    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    medical_topics: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ai_runs.id",
            name="fk_interactions_ai_runs",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    ai_raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[InteractionStatus] = mapped_column(
        Enum(
            InteractionStatus,
            name="interaction_status",
            values_callable=lambda obj: [e.value for e in obj],
            native_enum=True,
            create_type=False,
            create_constraint=False,
        ),
        nullable=False,
        server_default=text("'draft'::interaction_status"),
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    user: Mapped[User] = relationship(
        back_populates="interactions",
        foreign_keys=[user_id],
    )
    hcp: Mapped[HealthcareProfessional] = relationship(
        back_populates="interactions",
        foreign_keys=[hcp_id],
    )
    ai_run: Mapped[AiRun | None] = relationship(
        back_populates="saved_interactions",
        foreign_keys=[ai_run_id],
    )
    draft_ai_runs: Mapped[list[AiRun]] = relationship(
        back_populates="interaction",
        foreign_keys="AiRun.interaction_id",
    )
    products: Mapped[list[InteractionProduct]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )
    follow_ups: Mapped[list[FollowUp]] = relationship(
        back_populates="interaction",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Interaction id={self.id!s} status={self.status!s}>"


class InteractionProduct(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interaction_products"
    __table_args__ = (
        UniqueConstraint("interaction_id", "product_id", name="uq_interaction_products_pair"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_interaction_products_confidence",
        ),
        Index("ix_interaction_products_product_id", "product_id"),
    )

    interaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "interactions.id",
            name="fk_interaction_products_interactions",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            name="fk_interaction_products_products",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
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

    interaction: Mapped[Interaction] = relationship(back_populates="products")
    product: Mapped[Product] = relationship(back_populates="interaction_products")

    def __repr__(self) -> str:
        return (
            f"<InteractionProduct interaction_id={self.interaction_id!s} "
            f"product_id={self.product_id!s}>"
        )
