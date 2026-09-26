import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MissionCollaborator(Base):
    __tablename__ = "mission_collaborators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), default="COLLABORATOR", nullable=False) # OWNER, EDITOR, COLLABORATOR, VIEWER
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("mission_id", "user_id", name="uq_mission_collaborator"),
    )

    mission = relationship("Mission", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id], back_populates="collaborations")
    inviter = relationship("User", foreign_keys=[invited_by])


class CollaborationRequest(Base):
    __tablename__ = "collaboration_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=True)
    status = Column(String(30), default="PENDING", nullable=False) # PENDING, ACCEPTED, DECLINED, CANCELLED
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="collaboration_requests")
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
