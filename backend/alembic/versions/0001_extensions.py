"""Enable PostgreSQL extensions required by the schema.

Revision ID: 0001_extensions
Revises:
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001_extensions"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")


def downgrade() -> None:
    # Leave pgcrypto installed; dropping may affect other DBs sharing the cluster.
    pass
