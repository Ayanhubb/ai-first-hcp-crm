-- Init script mounted into Postgres via docker-entrypoint-initdb.d
-- Full schema evolves via Alembic (backend/alembic/versions/)
-- See docs/database_design.md §28 for authoritative DDL reference

CREATE EXTENSION IF NOT EXISTS pgcrypto;
