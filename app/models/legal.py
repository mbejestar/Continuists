import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MissionOwnershipDeclaration(Base):
    """
    Mandatory declaration required before a Mission can be submitted for marketplace listing.
    Ensures intellectual-property vetting, employer non-infringement, and POPIA declarations.
    """
    __tablename__ = "mission_ownership_declarations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    # Declarations requested by specification:
    created_myself = Column(Boolean, nullable=False)
    others_involved = Column(Boolean, nullable=False)
    created_during_employment = Column(Boolean, nullable=False)
    created_for_client = Column(Boolean, nullable=False)
    org_owns_rights = Column(Boolean, nullable=False)
    contains_confidential_info = Column(Boolean, nullable=False)
    contains_third_party_material = Column(Boolean, nullable=False)
    full_legal_declaration_confirmed = Column(Boolean, nullable=False)
    
    declaration_text = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    declared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="ownership_declaration")
    user = relationship("User")


class LegalAgreement(Base):
    """Versioned legal terms and policies."""
    __tablename__ = "legal_agreements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TERMS_OF_SERVICE, PRIVACY_POLICY, MARKETPLACE_AGREEMENT, PURCHASE_LICENSE_AGREEMENT, ACCEPTABLE_USE_POLICY
    agreement_type = Column(String(60), nullable=False)
    version = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    content_markdown = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    published_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("agreement_type", "version", name="uq_legal_agreement_type_version"),
    )


class UserAgreement(Base):
    """Tracks exact user consent with immutable timestamp and security metadata."""
    __tablename__ = "user_agreements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("legal_agreements.id", ondelete="RESTRICT"), nullable=False)
    agreement_version = Column(String(32), nullable=False)
    accepted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "agreement_id", "agreement_version", name="uq_user_agreement_instance"),
    )

    user = relationship("User", back_populates="user_agreements")
    agreement = relationship("LegalAgreement")
