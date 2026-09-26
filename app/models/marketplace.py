import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="RESTRICT"), unique=True, nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    proposed_value = Column(Numeric(15, 2), nullable=False)
    asking_price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="ZAR", nullable=False)
    
    # Fee tier: DIRECT (8%) or ASSISTED (15%)
    fee_tier = Column(String(20), default="DIRECT", nullable=False)
    
    # Status: DRAFT, SUBMITTED, UNDER_REVIEW, ADDITIONAL_INFORMATION_REQUIRED, APPROVED, REJECTED, WITHDRAWN
    status = Column(String(40), default="DRAFT", nullable=False, index=True)
    
    # Non-confidential public overview strictly permitted before purchase
    summary_non_confidential = Column(Text, nullable=False)
    industry = Column(String(100), nullable=False, index=True)
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="marketplace_listing")
    seller = relationship("User", foreign_keys=[seller_id])
    evaluations = relationship("MarketplaceEvaluation", back_populates="listing", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="listing")


class MarketplaceEvaluation(Base):
    __tablename__ = "marketplace_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(40), default="PENDING", nullable=False)
    
    # 10 Continuum evaluation dimensions (1-10 scale)
    score_originality = Column(Integer, nullable=True)
    score_completeness = Column(Integer, nullable=True)
    score_practical_usefulness = Column(Integer, nullable=True)
    score_technical_depth = Column(Integer, nullable=True)
    score_supporting_evidence = Column(Integer, nullable=True)
    score_uniqueness = Column(Integer, nullable=True)
    score_industry_relevance = Column(Integer, nullable=True)
    score_market_relevance = Column(Integer, nullable=True)
    score_ownership_rights = Column(Integer, nullable=True)
    score_documentation_quality = Column(Integer, nullable=True)
    
    weighted_total_score = Column(Numeric(5, 2), nullable=True)
    evaluation_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    listing = relationship("MarketplaceListing", back_populates="evaluations")
    evaluator = relationship("User", foreign_keys=[evaluator_id])
