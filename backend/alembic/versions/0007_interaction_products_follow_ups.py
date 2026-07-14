"""Create interaction_products and follow_ups tables.

Revision ID: 0007_interaction_products_follow_ups
Revises: 0006_interactions
Create Date: 2026-07-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_ix_products_follow_ups"
down_revision: Union[str, None] = "0006_interactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

record_source = postgresql.ENUM("ai", "manual", name="record_source", create_type=False)
follow_up_priority = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="follow_up_priority",
    create_type=False,
)
follow_up_status = postgresql.ENUM(
    "open",
    "done",
    "cancelled",
    name="follow_up_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "interaction_products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("interaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=True),
        sa.Column(
            "source",
            record_source,
            server_default=sa.text("'manual'::record_source"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_interaction_products_confidence",
        ),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interactions.id"],
            name="fk_interaction_products_interactions",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_interaction_products_products",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interaction_products"),
        sa.UniqueConstraint(
            "interaction_id",
            "product_id",
            name="uq_interaction_products_pair",
        ),
    )

    op.create_table(
        "follow_ups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("interaction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "priority",
            follow_up_priority,
            server_default=sa.text("'medium'::follow_up_priority"),
            nullable=False,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            follow_up_status,
            server_default=sa.text("'open'::follow_up_status"),
            nullable=False,
        ),
        sa.Column(
            "source",
            record_source,
            server_default=sa.text("'manual'::record_source"),
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
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_follow_ups_title_nonempty"),
        sa.ForeignKeyConstraint(
            ["interaction_id"],
            ["interactions.id"],
            name="fk_follow_ups_interactions",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_follow_ups_users",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_follow_ups"),
    )


def downgrade() -> None:
    op.drop_table("follow_ups")
    op.drop_table("interaction_products")
