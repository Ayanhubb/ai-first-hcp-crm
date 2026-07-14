"""Create all PostgreSQL enum types.

Revision ID: 0002_enums
Revises: 0001_extensions
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_enums"
down_revision: Union[str, None] = "0001_extensions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ENUMS: dict[str, tuple[str, ...]] = {
    "user_role": ("mr", "admin"),
    "visit_channel": ("in_person", "virtual", "phone"),
    "interaction_sentiment": ("positive", "neutral", "negative", "mixed"),
    "interaction_status": ("draft", "saved"),
    "record_source": ("ai", "manual"),
    "follow_up_priority": ("low", "medium", "high"),
    "follow_up_status": ("open", "done", "cancelled"),
    "ai_run_status": ("running", "succeeded", "failed", "partial"),
}


def upgrade() -> None:
    for name, values in ENUMS.items():
        values_sql = ", ".join(f"'{v}'" for v in values)
        op.execute(f"CREATE TYPE {name} AS ENUM ({values_sql})")


def downgrade() -> None:
    for name in reversed(list(ENUMS)):
        op.execute(f"DROP TYPE IF EXISTS {name}")
