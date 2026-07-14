-- =============================================================================
-- AI-First HCP CRM — PostgreSQL Baseline DDL
-- Source: docs/database_design.md §28
-- Migration source of truth: backend/alembic/versions/
-- This file is a readable mirror for review / greenfield bootstraps.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- Enums
-- -----------------------------------------------------------------------------

CREATE TYPE user_role AS ENUM ('mr', 'admin');
CREATE TYPE visit_channel AS ENUM ('in_person', 'virtual', 'phone');
CREATE TYPE interaction_sentiment AS ENUM ('positive', 'neutral', 'negative', 'mixed');
CREATE TYPE interaction_status AS ENUM ('draft', 'saved');
CREATE TYPE record_source AS ENUM ('ai', 'manual');
CREATE TYPE follow_up_priority AS ENUM ('low', 'medium', 'high');
CREATE TYPE follow_up_status AS ENUM ('open', 'done', 'cancelled');
CREATE TYPE ai_run_status AS ENUM ('running', 'succeeded', 'failed', 'partial');

-- -----------------------------------------------------------------------------
-- users
-- -----------------------------------------------------------------------------

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(320) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    role            user_role NOT NULL DEFAULT 'mr',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT ck_users_email_nonempty CHECK (length(trim(email)) > 0)
);

CREATE INDEX ix_users_role ON users (role);
CREATE INDEX ix_users_is_active ON users (is_active);

-- -----------------------------------------------------------------------------
-- auth_refresh_tokens
-- -----------------------------------------------------------------------------

CREATE TABLE auth_refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ NULL,
    user_agent      VARCHAR(512) NULL,
    ip_address      INET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_auth_refresh_tokens_token_hash UNIQUE (token_hash),
    CONSTRAINT ck_auth_refresh_expires_after_created CHECK (expires_at > created_at),
    CONSTRAINT fk_auth_refresh_tokens_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX ix_auth_refresh_tokens_user ON auth_refresh_tokens (user_id);
CREATE INDEX ix_auth_refresh_tokens_expires_at ON auth_refresh_tokens (expires_at);

-- -----------------------------------------------------------------------------
-- healthcare_professionals
-- -----------------------------------------------------------------------------

CREATE TABLE healthcare_professionals (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name            VARCHAR(100) NOT NULL,
    last_name             VARCHAR(100) NOT NULL,
    specialty             VARCHAR(150) NOT NULL,
    institution           VARCHAR(255) NULL,
    city                  VARCHAR(100) NULL,
    state                 VARCHAR(100) NULL,
    country               VARCHAR(100) NULL,
    email                 VARCHAR(320) NULL,
    phone                 VARCHAR(50) NULL,
    registration_number   VARCHAR(100) NULL,
    metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_hcps_registration_number UNIQUE (registration_number)
);

CREATE INDEX ix_hcps_last_name_first_name
    ON healthcare_professionals (last_name, first_name);
CREATE INDEX ix_hcps_specialty_city
    ON healthcare_professionals (specialty, city);

-- -----------------------------------------------------------------------------
-- products
-- -----------------------------------------------------------------------------

CREATE TABLE products (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code               VARCHAR(64) NOT NULL,
    name               VARCHAR(200) NOT NULL,
    therapeutic_area   VARCHAR(150) NULL,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_products_code UNIQUE (code),
    CONSTRAINT ck_products_code_nonempty CHECK (length(trim(code)) > 0)
);

CREATE INDEX ix_products_name ON products (name);
CREATE INDEX ix_products_is_active ON products (is_active)
    WHERE is_active = TRUE;

-- -----------------------------------------------------------------------------
-- ai_runs (interaction_id FK added after interactions)
-- -----------------------------------------------------------------------------

CREATE TABLE ai_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NULL,
    hcp_id            UUID NULL,
    interaction_id    UUID NULL,
    graph_name        VARCHAR(128) NOT NULL,
    status            ai_run_status NOT NULL DEFAULT 'running',
    model_name        VARCHAR(128) NOT NULL,
    latency_ms        INTEGER NULL,
    token_usage       JSONB NULL,
    error_message     TEXT NULL,
    state_snapshot    JSONB NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ NULL,
    CONSTRAINT ck_ai_runs_latency_nonneg CHECK (latency_ms IS NULL OR latency_ms >= 0),
    CONSTRAINT fk_ai_runs_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_ai_runs_hcps
        FOREIGN KEY (hcp_id) REFERENCES healthcare_professionals (id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX ix_ai_runs_user_created ON ai_runs (user_id, created_at DESC);
CREATE INDEX ix_ai_runs_hcp_created ON ai_runs (hcp_id, created_at DESC);
CREATE INDEX ix_ai_runs_status ON ai_runs (status);

-- -----------------------------------------------------------------------------
-- interactions
-- -----------------------------------------------------------------------------

CREATE TABLE interactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    hcp_id              UUID NOT NULL,
    visit_at            TIMESTAMPTZ NOT NULL,
    channel             visit_channel NOT NULL,
    notes               TEXT NOT NULL,
    summary             TEXT NULL,
    sentiment           interaction_sentiment NULL,
    sentiment_score     NUMERIC(4,3) NULL,
    medical_topics      JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_run_id           UUID NULL,
    ai_raw_payload      JSONB NULL,
    status              interaction_status NOT NULL DEFAULT 'draft',
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_interactions_sentiment_score
        CHECK (sentiment_score IS NULL OR (sentiment_score >= 0 AND sentiment_score <= 1)),
    CONSTRAINT ck_interactions_notes_nonempty_when_saved
        CHECK (status <> 'saved' OR length(trim(notes)) > 0),
    CONSTRAINT fk_interactions_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_interactions_hcps
        FOREIGN KEY (hcp_id) REFERENCES healthcare_professionals (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_interactions_ai_runs
        FOREIGN KEY (ai_run_id) REFERENCES ai_runs (id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX ix_interactions_user_id_visit_at
    ON interactions (user_id, visit_at DESC);
CREATE INDEX ix_interactions_hcp_id_visit_at
    ON interactions (hcp_id, visit_at DESC);
CREATE INDEX ix_interactions_not_deleted
    ON interactions (visit_at DESC)
    WHERE is_deleted = FALSE;
CREATE INDEX ix_interactions_status
    ON interactions (status)
    WHERE is_deleted = FALSE;

ALTER TABLE ai_runs
    ADD CONSTRAINT fk_ai_runs_interactions
    FOREIGN KEY (interaction_id) REFERENCES interactions (id)
    ON UPDATE CASCADE ON DELETE SET NULL;

CREATE INDEX ix_ai_runs_interaction_id ON ai_runs (interaction_id);

-- -----------------------------------------------------------------------------
-- interaction_products
-- -----------------------------------------------------------------------------

CREATE TABLE interaction_products (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id    UUID NOT NULL,
    product_id        UUID NOT NULL,
    confidence        NUMERIC(4,3) NULL,
    source            record_source NOT NULL DEFAULT 'manual',
    CONSTRAINT uq_interaction_products_pair UNIQUE (interaction_id, product_id),
    CONSTRAINT ck_interaction_products_confidence
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    CONSTRAINT fk_interaction_products_interactions
        FOREIGN KEY (interaction_id) REFERENCES interactions (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_interaction_products_products
        FOREIGN KEY (product_id) REFERENCES products (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX ix_interaction_products_product_id ON interaction_products (product_id);

-- -----------------------------------------------------------------------------
-- follow_ups
-- -----------------------------------------------------------------------------

CREATE TABLE follow_ups (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interaction_id    UUID NOT NULL,
    user_id           UUID NOT NULL,
    title             VARCHAR(255) NOT NULL,
    description       TEXT NULL,
    priority          follow_up_priority NOT NULL DEFAULT 'medium',
    due_at            TIMESTAMPTZ NULL,
    status            follow_up_status NOT NULL DEFAULT 'open',
    source            record_source NOT NULL DEFAULT 'manual',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_follow_ups_title_nonempty CHECK (length(trim(title)) > 0),
    CONSTRAINT fk_follow_ups_interactions
        FOREIGN KEY (interaction_id) REFERENCES interactions (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_follow_ups_users
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX ix_follow_ups_user_status_due
    ON follow_ups (user_id, status, due_at);
CREATE INDEX ix_follow_ups_interaction_id ON follow_ups (interaction_id);

-- -----------------------------------------------------------------------------
-- audit_logs
-- -----------------------------------------------------------------------------

CREATE TABLE audit_logs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id     UUID NULL,
    entity_type       VARCHAR(64) NOT NULL,
    entity_id         UUID NOT NULL,
    action            VARCHAR(64) NOT NULL,
    before_state      JSONB NULL,
    after_state       JSONB NULL,
    ip_address        INET NULL,
    correlation_id    UUID NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_audit_logs_users
        FOREIGN KEY (actor_user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE INDEX ix_audit_logs_entity_created
    ON audit_logs (entity_type, entity_id, created_at DESC);
CREATE INDEX ix_audit_logs_actor_created
    ON audit_logs (actor_user_id, created_at DESC);
CREATE INDEX ix_audit_logs_correlation_id
    ON audit_logs (correlation_id);

CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_logs_no_update
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

-- -----------------------------------------------------------------------------
-- updated_at helper
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_hcps_updated_at
    BEFORE UPDATE ON healthcare_professionals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_interactions_updated_at
    BEFORE UPDATE ON interactions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_follow_ups_updated_at
    BEFORE UPDATE ON follow_ups
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
