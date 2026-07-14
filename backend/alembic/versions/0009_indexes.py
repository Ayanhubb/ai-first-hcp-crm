"""Create indexes and updated_at triggers.

Revision ID: 0009_indexes
Revises: 0008_audit_logs
Create Date: 2026-07-14
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0009_indexes"
down_revision: Union[str, None] = "0008_audit_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # --- auth_refresh_tokens ---
    op.create_index("ix_auth_refresh_tokens_user", "auth_refresh_tokens", ["user_id"])
    op.create_index("ix_auth_refresh_tokens_expires_at", "auth_refresh_tokens", ["expires_at"])

    # --- healthcare_professionals ---
    op.create_index(
        "ix_hcps_last_name_first_name",
        "healthcare_professionals",
        ["last_name", "first_name"],
    )
    op.create_index(
        "ix_hcps_specialty_city",
        "healthcare_professionals",
        ["specialty", "city"],
    )

    # --- products ---
    op.create_index("ix_products_name", "products", ["name"])
    op.execute(
        "CREATE INDEX ix_products_is_active ON products (is_active) WHERE is_active = TRUE"
    )

    # --- ai_runs ---
    op.execute(
        "CREATE INDEX ix_ai_runs_user_created ON ai_runs (user_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_ai_runs_hcp_created ON ai_runs (hcp_id, created_at DESC)"
    )
    op.create_index("ix_ai_runs_status", "ai_runs", ["status"])
    op.create_index("ix_ai_runs_interaction_id", "ai_runs", ["interaction_id"])

    # --- interactions ---
    op.execute(
        "CREATE INDEX ix_interactions_user_id_visit_at "
        "ON interactions (user_id, visit_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_interactions_hcp_id_visit_at "
        "ON interactions (hcp_id, visit_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_interactions_not_deleted "
        "ON interactions (visit_at DESC) WHERE is_deleted = FALSE"
    )
    op.execute(
        "CREATE INDEX ix_interactions_status "
        "ON interactions (status) WHERE is_deleted = FALSE"
    )

    # --- interaction_products ---
    op.create_index(
        "ix_interaction_products_product_id",
        "interaction_products",
        ["product_id"],
    )

    # --- follow_ups ---
    op.create_index(
        "ix_follow_ups_user_status_due",
        "follow_ups",
        ["user_id", "status", "due_at"],
    )
    op.create_index("ix_follow_ups_interaction_id", "follow_ups", ["interaction_id"])

    # --- audit_logs ---
    op.execute(
        "CREATE INDEX ix_audit_logs_entity_created "
        "ON audit_logs (entity_type, entity_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_audit_logs_actor_created "
        "ON audit_logs (actor_user_id, created_at DESC)"
    )
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])

    # --- updated_at helper ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table, trigger in (
        ("users", "trg_users_updated_at"),
        ("healthcare_professionals", "trg_hcps_updated_at"),
        ("products", "trg_products_updated_at"),
        ("interactions", "trg_interactions_updated_at"),
        ("follow_ups", "trg_follow_ups_updated_at"),
    ):
        op.execute(
            f"""
            CREATE TRIGGER {trigger}
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION set_updated_at();
            """
        )


def downgrade() -> None:
    for table, trigger in (
        ("follow_ups", "trg_follow_ups_updated_at"),
        ("interactions", "trg_interactions_updated_at"),
        ("products", "trg_products_updated_at"),
        ("healthcare_professionals", "trg_hcps_updated_at"),
        ("users", "trg_users_updated_at"),
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON {table}")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_actor_created")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_entity_created")

    op.drop_index("ix_follow_ups_interaction_id", table_name="follow_ups")
    op.drop_index("ix_follow_ups_user_status_due", table_name="follow_ups")

    op.drop_index("ix_interaction_products_product_id", table_name="interaction_products")

    op.execute("DROP INDEX IF EXISTS ix_interactions_status")
    op.execute("DROP INDEX IF EXISTS ix_interactions_not_deleted")
    op.execute("DROP INDEX IF EXISTS ix_interactions_hcp_id_visit_at")
    op.execute("DROP INDEX IF EXISTS ix_interactions_user_id_visit_at")

    op.drop_index("ix_ai_runs_interaction_id", table_name="ai_runs")
    op.drop_index("ix_ai_runs_status", table_name="ai_runs")
    op.execute("DROP INDEX IF EXISTS ix_ai_runs_hcp_created")
    op.execute("DROP INDEX IF EXISTS ix_ai_runs_user_created")

    op.execute("DROP INDEX IF EXISTS ix_products_is_active")
    op.drop_index("ix_products_name", table_name="products")

    op.drop_index("ix_hcps_specialty_city", table_name="healthcare_professionals")
    op.drop_index("ix_hcps_last_name_first_name", table_name="healthcare_professionals")

    op.drop_index("ix_auth_refresh_tokens_expires_at", table_name="auth_refresh_tokens")
    op.drop_index("ix_auth_refresh_tokens_user", table_name="auth_refresh_tokens")

    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
