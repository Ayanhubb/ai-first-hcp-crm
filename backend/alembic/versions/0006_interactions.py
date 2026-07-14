"""Create interactions table and ai_runs.interaction_id FK.

Revision ID: 0006_interactions
Revises: 0005_ai_runs
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_interactions"
down_revision: Union[str, None] = "0005_ai_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

visit_channel = postgresql.ENUM(
    "in_person",
    "virtual",
    "phone",
    name="visit_channel",
    create_type=False,
)
interaction_sentiment = postgresql.ENUM(
    "positive",
    "neutral",
    "negative",
    "mixed",
    name="interaction_sentiment",
    create_type=False,
)
interaction_status = postgresql.ENUM(
    "draft",
    "saved",
    name="interaction_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "interactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hcp_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", visit_channel, nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment", interaction_sentiment, nullable=True),
        sa.Column("sentiment_score", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "medical_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("ai_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            interaction_status,
            server_default=sa.text("'draft'::interaction_status"),
            nullable=False,
        ),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sentiment_score IS NULL OR (sentiment_score >= 0 AND sentiment_score <= 1)",
            name="ck_interactions_sentiment_score",
        ),
        sa.CheckConstraint(
            "status <> 'saved' OR length(trim(notes)) > 0",
            name="ck_interactions_notes_nonempty_when_saved",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_interactions_users",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["hcp_id"],
            ["healthcare_professionals.id"],
            name="fk_interactions_hcps",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ai_run_id"],
            ["ai_runs.id"],
            name="fk_interactions_ai_runs",
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interactions"),
    )

    op.create_foreign_key(
        "fk_ai_runs_interactions",
        "ai_runs",
        "interactions",
        ["interaction_id"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_runs_interactions", "ai_runs", type_="foreignkey")
    op.drop_table("interactions")
