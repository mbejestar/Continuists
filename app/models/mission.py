import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MissionVisibility(str, Enum):
    PRIVATE = "PRIVATE"
    PUBLIC = "PUBLIC"

class Mission(Base):
    __tablename__ = "missions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    continuum_id = Column(String(20), unique=True, nullable=False, index=True) # e.g. MSN-9A23-K7M1
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # 1. Mission Heading
    heading = Column(String(255), nullable=False)
    
    # 2. Problem Being Solved (Optional manual typing vs documents)
    problem_statement = Column(Text, nullable=True)
    
    # 3. What We Found
    what_we_found = Column(Text, nullable=True)
    
    # 4. Lessons Learned
    lessons_learned = Column(Text, nullable=True)
    
    # 5. Project Value
    project_value_est = Column(Numeric(15, 2), default=0.00, nullable=False)
    currency = Column(String(3), default="ZAR", nullable=False)
    
    # 6. Amount Spent / Invested
    amount_spent = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # 7. Visibility: PRIVATE by default
    visibility = Column(String(20), default="PRIVATE", nullable=False, index=True)
    
    # 8. Collaboration settings
    collaboration_open = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="owned_missions", foreign_keys=[owner_id])
    documents = relationship("MissionDocument", back_populates="mission", cascade="all, delete-orphan")
    collaborators = relationship("MissionCollaborator", back_populates="mission", cascade="all, delete-orphan")
    collaboration_requests = relationship("CollaborationRequest", back_populates="mission", cascade="all, delete-orphan")
    release_rule = relationship("MissionReleaseRule", back_populates="mission", uselist=False, cascade="all, delete-orphan")
    successor = relationship("MissionSuccessor", back_populates="mission", uselist=False, cascade="all, delete-orphan")
    ownership_declaration = relationship("MissionOwnershipDeclaration", back_populates="mission", uselist=False, cascade="all, delete-orphan")
    marketplace_listing = relationship("MarketplaceListing", back_populates="mission", uselist=False)
    access_grants = relationship("MissionAccess", back_populates="mission", cascade="all, delete-orphan")
