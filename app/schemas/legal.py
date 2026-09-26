from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class OwnershipDeclarationRequest(BaseModel):
    created_myself: bool = Field(..., description="Did you create this work yourself?")
    others_involved: bool = Field(..., description="Were other people involved?")
    created_during_employment: bool = Field(..., description="Was the work created during employment?")
    created_for_client: bool = Field(..., description="Was it created for a client?")
    org_owns_rights: bool = Field(..., description="Does another organisation own rights in this material?")
    contains_confidential_info: bool = Field(..., description="Does the Mission contain confidential information?")
    contains_third_party_material: bool = Field(..., description="Does the Mission contain third-party material?")
    full_legal_declaration_confirmed: bool = Field(..., description="Confirm necessary rights and permissions to upload, publish, and sell")
    declaration_text: str = Field(..., min_length=20, max_length=2000)

class OwnershipDeclarationResponse(BaseModel):
    id: UUID
    mission_id: UUID
    created_myself: bool
    others_involved: bool
    created_during_employment: bool
    created_for_client: bool
    org_owns_rights: bool
    contains_confidential_info: bool
    contains_third_party_material: bool
    full_legal_declaration_confirmed: bool
    declared_at: datetime

    class Config:
        from_attributes = True

class LegalAgreementResponse(BaseModel):
    id: UUID
    agreement_type: str
    version: str
    title: str
    content_markdown: str
    published_at: datetime

    class Config:
        from_attributes = True

class UserAgreementAcceptance(BaseModel):
    agreement_id: UUID
    agreement_version: str
