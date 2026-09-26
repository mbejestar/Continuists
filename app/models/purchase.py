import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="RESTRICT"), nullable=False)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    gross_amount = Column(Numeric(15, 2), nullable=False)
    platform_fee_amount = Column(Numeric(15, 2), nullable=False)
    platform_fee_rate = Column(Numeric(4, 2), nullable=False) # 0.08 or 0.15
    seller_net_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="ZAR", nullable=False)
    
    fee_tier = Column(String(20), nullable=False) # DIRECT or ASSISTED
    license_type = Column(String(50), nullable=False) # ACCESS_LICENCE, LIMITED_USE_LICENCE, ASSIGNMENT_OF_SPECIFIED_RIGHTS
    payment_reference = Column(String(255), unique=True, nullable=False)
    payment_status = Column(String(40), default="PENDING", nullable=False)
    agreement_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    listing = relationship("MarketplaceListing", back_populates="purchases")
    mission = relationship("Mission")
    buyer = relationship("User", foreign_keys=[buyer_id])
    seller = relationship("User", foreign_keys=[seller_id])
    access_grant = relationship("MissionAccess", back_populates="purchase", uselist=False)


class MissionAccess(Base):
    __tablename__ = "mission_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Access types: OWNER, COLLABORATOR, PURCHASER, VIEWER
    access_type = Column(String(30), default="PURCHASER", nullable=False)
    license_type = Column(String(50), nullable=True)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True)
    
    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("mission_id", "user_id", "access_type", name="uq_mission_user_access_grant"),
    )

    mission = relationship("Mission", back_populates="access_grants")
    user = relationship("User")
    purchase = relationship("Purchase", back_populates="access_grant")
