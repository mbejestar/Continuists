from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class CollaborationRequestCreate(BaseModel):
    message: Optional[str] = Field(None, max_length=1000)

class InviteCollaboratorRequest(BaseModel):
    user_continuum_id_or_email: str
    role: str = Field("COLLABORATOR", pattern="^(EDITOR|COLLABORATOR|VIEWER)$")

class CollaborationResponse(BaseModel):
    id: UUID
    mission_id: UUID
    requester_id: UUID
    message: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CollaboratorMemberResponse(BaseModel):
    id: UUID
    mission_id: UUID
    user_id: UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
