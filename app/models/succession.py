import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MissionReleaseRule(Base):
    __tablename__ = "mission_release_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    inactivity_period_value = Column(Integer, default=5, nullable=False)
    inactivity_period_unit = Column(String(20), default="YEARS", nullable=False) # 'MONTHS' or 'YEARS'
    is_enabled = Column(Boolean, default=False, nullable=False)
    
    calculated_release_date = Column(DateTime(timezone=True), nullable=True)
    last_warning_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_reset_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="release_rule")


class MissionSuccessor(Base):
    __tablename__ = "mission_successors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    relationship = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    alternative_contact = Column(String(255), nullable=True)
    
    # Intended actions:
    # KEEP_PRIVATE, TRANSFER_MANAGEMENT_SUBJECT_TO_LEGAL_VERIFICATION, PREPARE_FOR_MARKETPLACE_RELEASE, CONTACT_NOMINATED_PERSON
    intended_action = Column(String(60), default="KEEP_PRIVATE", nullable=False)
    
    # Legal clarity: Nominated person does NOT automatically become owner without estate verification
    legal_notice_acknowledged = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="successor")
