-- ============================================================================
-- CONTINUUM KNOWLEDGE PRESERVATION & MARKETPLACE PLATFORM
-- PostgreSQL Database Schema (Production Ready DDL)
-- "The files remain. The context doesn't."
-- Designed for South African POPIA Compliance, Intellectual Property Protection,
-- Inactivity Release Rules, Succession Planning, and Controlled Marketplace.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Clean drop for idempotency if running in a fresh development database
-- DO NOT RUN DROPS IN PRODUCTION

-- ----------------------------------------------------------------------------
-- 1. ENUMS
-- ----------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE user_subscription_enum AS ENUM ('FREE', 'PREMIUM');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE mission_visibility_enum AS ENUM ('PRIVATE', 'PUBLIC');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE mission_role_enum AS ENUM ('OWNER', 'EDITOR', 'COLLABORATOR', 'VIEWER');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE collaboration_status_enum AS ENUM ('PENDING', 'ACCEPTED', 'DECLINED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE marketplace_status_enum AS ENUM (
        'DRAFT',
        'SUBMITTED',
        'UNDER_REVIEW',
        'ADDITIONAL_INFORMATION_REQUIRED',
        'APPROVED',
        'REJECTED',
        'WITHDRAWN'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE fee_tier_enum AS ENUM ('DIRECT', 'ASSISTED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE license_type_enum AS ENUM (
        'ACCESS_LICENCE',
        'LIMITED_USE_LICENCE',
        'ASSIGNMENT_OF_SPECIFIED_RIGHTS'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE access_type_enum AS ENUM ('OWNER', 'COLLABORATOR', 'PURCHASER', 'VIEWER');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE succession_action_enum AS ENUM (
        'KEEP_PRIVATE',
        'TRANSFER_MANAGEMENT_SUBJECT_TO_LEGAL_VERIFICATION',
        'PREPARE_FOR_MARKETPLACE_RELEASE',
        'CONTACT_NOMINATED_PERSON'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE release_unit_enum AS ENUM ('MONTHS', 'YEARS');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE agreement_type_enum AS ENUM (
        'TERMS_OF_SERVICE',
        'PRIVACY_POLICY',
        'MARKETPLACE_AGREEMENT',
        'PURCHASE_LICENSE_AGREEMENT',
        'ACCEPTABLE_USE_POLICY'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ----------------------------------------------------------------------------
-- 2. USERS & PROFILES
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    continuum_id VARCHAR(16) NOT NULL UNIQUE, -- e.g. CNT-7F42-91K8
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    country VARCHAR(100) NOT NULL DEFAULT 'South Africa',
    province_region VARCHAR(100),
    profile_photo_url TEXT,
    subscription user_subscription_enum NOT NULL DEFAULT 'FREE',
    subscription_renews_at TIMESTAMPTZ,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_continuum_id ON users(continuum_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ----------------------------------------------------------------------------
-- 3. USER SETTINGS & PREFERENCES
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    dark_mode BOOLEAN NOT NULL DEFAULT FALSE, -- strictly false by default
    email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
    release_reminder_days INT NOT NULL DEFAULT 30,
    popia_consent_at TIMESTAMPTZ,
    biometric_recovery_enabled BOOLEAN NOT NULL DEFAULT FALSE, -- opt-in only
    biometric_credential_id TEXT, -- zero raw data stored
    recovery_codes_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. MISSIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    continuum_id VARCHAR(20) NOT NULL UNIQUE, -- e.g. MSN-9A23-K7M1
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    heading VARCHAR(255) NOT NULL,
    problem_statement TEXT,
    what_we_found TEXT,
    lessons_learned TEXT,
    project_value_est NUMERIC(15, 2) DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    amount_spent NUMERIC(15, 2) DEFAULT 0.00,
    visibility mission_visibility_enum NOT NULL DEFAULT 'PRIVATE', -- PRIVATE by default
    collaboration_open BOOLEAN NOT NULL DEFAULT FALSE,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_missions_owner_id ON missions(owner_id);
CREATE INDEX IF NOT EXISTS idx_missions_visibility ON missions(visibility);
CREATE INDEX IF NOT EXISTS idx_missions_last_activity ON missions(last_activity_at);

-- ----------------------------------------------------------------------------
-- 5. MISSION DOCUMENTS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mission_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    uploader_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_path VARCHAR(512) NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    is_confidential BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_mission_id ON mission_documents(mission_id);
CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON mission_documents(sha256_hash);

-- ----------------------------------------------------------------------------
-- 6. MISSION COLLABORATORS & REQUESTS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mission_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role mission_role_enum NOT NULL DEFAULT 'COLLABORATOR',
    invited_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_mission_user_role UNIQUE (mission_id, user_id)
);

CREATE TABLE IF NOT EXISTS collaboration_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT,
    status collaboration_status_enum NOT NULL DEFAULT 'PENDING',
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collab_req_mission ON collaboration_requests(mission_id);
CREATE INDEX IF NOT EXISTS idx_collab_req_requester ON collaboration_requests(requester_id);

-- ----------------------------------------------------------------------------
-- 7. MESSAGES (With Mission Context)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    mission_id UUID REFERENCES missions(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_participants ON messages(sender_id, recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_mission ON messages(mission_id);

-- ----------------------------------------------------------------------------
-- 8. NOTIFICATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(64) NOT NULL,
    reference_type VARCHAR(64),
    reference_id UUID,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);

-- ----------------------------------------------------------------------------
-- 9. MARKETPLACE LISTINGS & EVALUATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS marketplace_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL UNIQUE REFERENCES missions(id) ON DELETE RESTRICT,
    seller_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    proposed_value NUMERIC(15, 2) NOT NULL,
    asking_price NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    fee_tier fee_tier_enum NOT NULL DEFAULT 'DIRECT', -- DIRECT: 8%, ASSISTED: 15%
    status marketplace_status_enum NOT NULL DEFAULT 'DRAFT',
    summary_non_confidential TEXT NOT NULL,
    industry VARCHAR(100) NOT NULL,
    admin_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_marketplace_status ON marketplace_listings(status);
CREATE INDEX IF NOT EXISTS idx_marketplace_industry ON marketplace_listings(industry);

CREATE TABLE IF NOT EXISTS marketplace_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(id) ON DELETE CASCADE,
    evaluator_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    score_originality INT CHECK (score_originality BETWEEN 1 AND 10),
    score_completeness INT CHECK (score_completeness BETWEEN 1 AND 10),
    score_practical_usefulness INT CHECK (score_practical_usefulness BETWEEN 1 AND 10),
    score_technical_depth INT CHECK (score_technical_depth BETWEEN 1 AND 10),
    score_supporting_evidence INT CHECK (score_supporting_evidence BETWEEN 1 AND 10),
    score_uniqueness INT CHECK (score_uniqueness BETWEEN 1 AND 10),
    score_industry_relevance INT CHECK (score_industry_relevance BETWEEN 1 AND 10),
    score_market_relevance INT CHECK (score_market_relevance BETWEEN 1 AND 10),
    score_ownership_rights INT CHECK (score_ownership_rights BETWEEN 1 AND 10),
    score_documentation_quality INT CHECK (score_documentation_quality BETWEEN 1 AND 10),
    weighted_total_score NUMERIC(5, 2),
    evaluation_notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 10. PURCHASES & MISSION ACCESS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES marketplace_listings(id) ON DELETE RESTRICT,
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE RESTRICT,
    buyer_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    seller_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    gross_amount NUMERIC(15, 2) NOT NULL,
    platform_fee_amount NUMERIC(15, 2) NOT NULL,
    platform_fee_rate NUMERIC(4, 2) NOT NULL, -- 0.08 or 0.15
    seller_net_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'ZAR',
    fee_tier fee_tier_enum NOT NULL,
    license_type license_type_enum NOT NULL,
    payment_reference VARCHAR(255) NOT NULL UNIQUE,
    payment_status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    agreement_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mission_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_type access_type_enum NOT NULL DEFAULT 'PURCHASER',
    license_type VARCHAR(64),
    purchase_id UUID REFERENCES purchases(id) ON DELETE SET NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_mission_user_access UNIQUE (mission_id, user_id, access_type)
);

CREATE INDEX IF NOT EXISTS idx_mission_access_user ON mission_access(user_id, mission_id);

-- ----------------------------------------------------------------------------
-- 11. INACTIVITY RELEASE RULES & SUCCESSION
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mission_release_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL UNIQUE REFERENCES missions(id) ON DELETE CASCADE,
    inactivity_period_value INT NOT NULL DEFAULT 5,
    inactivity_period_unit release_unit_enum NOT NULL DEFAULT 'YEARS',
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_release_date TIMESTAMPTZ,
    last_warning_sent_at TIMESTAMPTZ,
    last_activity_reset_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mission_successors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL UNIQUE REFERENCES missions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    relationship VARCHAR(100) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    alternative_contact VARCHAR(255),
    intended_action succession_action_enum NOT NULL DEFAULT 'KEEP_PRIVATE',
    legal_notice_acknowledged BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 12. OWNERSHIP DECLARATIONS & LEGAL AGREEMENTS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mission_ownership_declarations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL UNIQUE REFERENCES missions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_myself BOOLEAN NOT NULL,
    others_involved BOOLEAN NOT NULL,
    created_during_employment BOOLEAN NOT NULL,
    created_for_client BOOLEAN NOT NULL,
    org_owns_rights BOOLEAN NOT NULL,
    contains_confidential_info BOOLEAN NOT NULL,
    contains_third_party_material BOOLEAN NOT NULL,
    full_legal_declaration_confirmed BOOLEAN NOT NULL,
    declaration_text TEXT NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    declared_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legal_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_type agreement_type_enum NOT NULL,
    version VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content_markdown TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    published_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_agreement_type_version UNIQUE (agreement_type, version)
);

CREATE TABLE IF NOT EXISTS user_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agreement_id UUID NOT NULL REFERENCES legal_agreements(id) ON DELETE RESTRICT,
    agreement_version VARCHAR(32) NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    CONSTRAINT uq_user_agreement_version UNIQUE (user_id, agreement_id, agreement_version)
);

-- ----------------------------------------------------------------------------
-- 13. AUDIT LOGS (POPIA & Security Immutable Trail)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL,
    entity VARCHAR(64) NOT NULL,
    entity_id UUID,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);
