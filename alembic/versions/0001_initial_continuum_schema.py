"""Initial Continuum Schema Migration

Revision ID: 0001_initial_continuum_schema
Revises: None
Create Date: 2026-09-25 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_continuum_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("continuum_id", sa.String(16), nullable=False, unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="South Africa"),
        sa.Column("province_region", sa.String(100), nullable=True),
        sa.Column("profile_photo_url", sa.Text(), nullable=True),
        sa.Column("subscription", sa.String(20), nullable=False, server_default="FREE"),
        sa.Column("subscription_renews_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_continuum_id", "users", ["continuum_id"])
    op.create_index("idx_users_email", "users", ["email"])

    # User Settings table
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("dark_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("release_reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("popia_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("biometric_recovery_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("biometric_credential_id", sa.Text(), nullable=True),
        sa.Column("recovery_codes_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Missions table
    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("continuum_id", sa.String(20), nullable=False, unique=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("heading", sa.String(255), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("what_we_found", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("project_value_est", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ZAR"),
        sa.Column("amount_spent", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="PRIVATE"),
        sa.Column("collaboration_open", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_missions_owner_id", "missions", ["owner_id"])
    op.create_index("idx_missions_visibility", "missions", ["visibility"])

    # Mission Documents table
    op.create_table(
        "mission_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_documents_mission_id", "mission_documents", ["mission_id"])

    # Mission Collaborators
    op.create_table(
        "mission_collaborators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="COLLABORATOR"),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("mission_id", "user_id", name="uq_mission_user_collab")
    )

    # Collaboration Requests
    op.create_table(
        "collaboration_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(64), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Marketplace Listings
    op.create_table(
        "marketplace_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="RESTRICT"), unique=True, nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proposed_value", sa.Numeric(15, 2), nullable=False),
        sa.Column("asking_price", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ZAR"),
        sa.Column("fee_tier", sa.String(20), nullable=False, server_default="DIRECT"),
        sa.Column("status", sa.String(40), nullable=False, server_default="DRAFT"),
        sa.Column("summary_non_confidential", sa.Text(), nullable=False),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Marketplace Evaluations
    op.create_table(
        "marketplace_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("score_originality", sa.Integer(), nullable=True),
        sa.Column("score_completeness", sa.Integer(), nullable=True),
        sa.Column("score_practical_usefulness", sa.Integer(), nullable=True),
        sa.Column("score_technical_depth", sa.Integer(), nullable=True),
        sa.Column("score_supporting_evidence", sa.Integer(), nullable=True),
        sa.Column("score_uniqueness", sa.Integer(), nullable=True),
        sa.Column("score_industry_relevance", sa.Integer(), nullable=True),
        sa.Column("score_market_relevance", sa.Integer(), nullable=True),
        sa.Column("score_ownership_rights", sa.Integer(), nullable=True),
        sa.Column("score_documentation_quality", sa.Integer(), nullable=True),
        sa.Column("weighted_total_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Purchases
    op.create_table(
        "purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_listings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("buyer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("gross_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("platform_fee_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("platform_fee_rate", sa.Numeric(4, 2), nullable=False),
        sa.Column("seller_net_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ZAR"),
        sa.Column("fee_tier", sa.String(20), nullable=False),
        sa.Column("license_type", sa.String(50), nullable=False),
        sa.Column("payment_reference", sa.String(255), nullable=False, unique=True),
        sa.Column("payment_status", sa.String(40), nullable=False, server_default="PENDING"),
        sa.Column("agreement_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Mission Access
    op.create_table(
        "mission_access",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_type", sa.String(30), nullable=False, server_default="PURCHASER"),
        sa.Column("license_type", sa.String(50), nullable=True),
        sa.Column("purchase_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("mission_id", "user_id", "access_type", name="uq_mission_user_access_tier")
    )

    # Succession & Release
    op.create_table(
        "mission_release_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("inactivity_period_value", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("inactivity_period_unit", sa.String(20), nullable=False, server_default="YEARS"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("calculated_release_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_warning_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_reset_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "mission_successors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("relationship", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("alternative_contact", sa.String(255), nullable=True),
        sa.Column("intended_action", sa.String(60), nullable=False, server_default="KEEP_PRIVATE"),
        sa.Column("legal_notice_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Ownership Declaration
    op.create_table(
        "mission_ownership_declarations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_myself", sa.Boolean(), nullable=False),
        sa.Column("others_involved", sa.Boolean(), nullable=False),
        sa.Column("created_during_employment", sa.Boolean(), nullable=False),
        sa.Column("created_for_client", sa.Boolean(), nullable=False),
        sa.Column("org_owns_rights", sa.Boolean(), nullable=False),
        sa.Column("contains_confidential_info", sa.Boolean(), nullable=False),
        sa.Column("contains_third_party_material", sa.Boolean(), nullable=False),
        sa.Column("full_legal_declaration_confirmed", sa.Boolean(), nullable=False),
        sa.Column("declaration_text", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("declared_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Legal Agreements
    op.create_table(
        "legal_agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agreement_type", sa.String(60), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agreement_type", "version", name="uq_agreement_type_version_idx")
    )

    op.create_table(
        "user_agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("legal_agreements.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("agreement_version", sa.String(32), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "agreement_id", "agreement_version", name="uq_user_agreement_instance_idx")
    )

    # Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}" ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_user_action", "audit_logs", ["user_id", "action"])
    op.create_index("idx_audit_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_agreements")
    op.drop_table("legal_agreements")
    op.drop_table("mission_ownership_declarations")
    op.drop_table("mission_successors")
    op.drop_table("mission_release_rules")
    op.drop_table("mission_access")
    op.drop_table("purchases")
    op.drop_table("marketplace_evaluations")
    op.drop_table("marketplace_listings")
    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("collaboration_requests")
    op.drop_table("mission_collaborators")
    op.drop_table("mission_documents")
    op.drop_table("missions")
    op.drop_table("user_settings")
    op.drop_table("users")
