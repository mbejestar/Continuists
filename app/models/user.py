import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class SubscriptionTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    continuum_id = Column(String(16), unique=True, nullable=False, index=True) # e.g. CNT-7F42-91K8
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(100), nullable=False, default="South Africa")
    province_region = Column(String(100), nullable=True) # e.g. Gauteng, Western Cape
    profile_photo_url = Column(Text, nullable=True)
    subscription = Column(String(20), nullable=False, default="FREE")
    subscription_renews_at = Column(DateTime(timezone=True), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    owned_missions = relationship("Mission", back_populates="owner", foreign_keys="Mission.owner_id")
    collaborations = relationship("MissionCollaborator", back_populates="user", cascade="all, delete-orphan", foreign_keys="MissionCollaborator.user_id")
    sent_messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    received_messages = relationship("Message", back_populates="recipient", foreign_keys="Message.recipient_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    user_agreements = relationship("UserAgreement", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    dark_mode = Column(Boolean, default=False, nullable=False) # strictly false by default
    email_notifications = Column(Boolean, default=True, nullable=False)
    release_reminder_days = Column(Integer, default=30, nullable=False)
    popia_consent_at = Column(DateTime(timezone=True), nullable=True)
    biometric_recovery_enabled = Column(Boolean, default=False, nullable=False) # opt-in only
    biometric_credential_id = Column(Text, nullable=True) # zero raw data stored
    recovery_codes_hash = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="settings")
