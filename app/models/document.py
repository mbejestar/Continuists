import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MissionDocument(Base):
    __tablename__ = "mission_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String(512), nullable=False) # Remote object URI or path
    sha256_hash = Column(String(64), nullable=False, index=True)
    is_confidential = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    mission = relationship("Mission", back_populates="documents")
    uploader = relationship("User")
