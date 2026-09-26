from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

class InactivityRuleCreate(BaseModel):
    inactivity_period_value: int = Field(5, ge=1, le=100)
    inactivity_period_unit: str = Field("YEARS", pattern="^(MONTHS|YEARS)$")
    is_enabled: bool = False

class SuccessionContactCreate(BaseModel):
    name: str
    relationship: str
    phone: str
    email: str
    alternative_contact: Optional[str] = None
    intended_action: str = Field(
        "KEEP_PRIVATE",
        pattern="^(KEEP_PRIVATE|TRANSFER_MANAGEMENT_SUBJECT_TO_LEGAL_VERIFICATION|PREPARE_FOR_MARKETPLACE_RELEASE|CONTACT_NOMINATED_PERSON)$"
    )
    legal_notice_acknowledged: bool = True

class MissionCreate(BaseModel):
    # 1. Mission Heading (Required)
    heading: str = Field(..., min_length=3, max_length=255)
    
    # 2. Problem Being Solved (Optional - manual typing not mandatory)
    problem_statement: Optional[str] = None
    
    # 3. What We Found (Optional)
    what_we_found: Optional[str] = None
    
    # 4. Lessons Learned (Optional)
    lessons_learned: Optional[str] = None
    
    # 5. Project Value
    project_value_est: Decimal = Field(Decimal("0.00"), ge=0)
    currency: str = "ZAR"
    
    # 6. Amount Spent / Invested
    amount_spent: Decimal = Field(Decimal("0.00"), ge=0)
    
    # 7. Visibility (Strictly PRIVATE by default)
    visibility: str = Field("PRIVATE", pattern="^(PRIVATE|PUBLIC)$")
    
    # 8. Collaboration settings
    collaboration_open: bool = False
    
    # 10. Inactivity / release settings
    release_rule: Optional[InactivityRuleCreate] = None
    
    # 11. Succession settings
    successor: Optional[SuccessionContactCreate] = None

class MissionUpdate(BaseModel):
    heading: Optional[str] = None
    problem_statement: Optional[str] = None
    what_we_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    project_value_est: Optional[Decimal] = None
    amount_spent: Optional[Decimal] = None
    visibility: Optional[str] = Field(None, pattern="^(PRIVATE|PUBLIC)$")
    collaboration_open: Optional[bool] = None

class MissionDocumentResponse(BaseModel):
    id: UUID
    mission_id: UUID
    original_filename: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str
    is_confidential: bool
    created_at: datetime

    class Config:
        from_attributes = True

class MissionDetailResponse(BaseModel):
    id: UUID
    continuum_id: str
    owner_id: UUID
    heading: str
    problem_statement: Optional[str] = None
    what_we_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    project_value_est: Decimal
    currency: str
    amount_spent: Decimal
    visibility: str
    collaboration_open: bool
    is_archived: bool
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Associated items
    documents: List[MissionDocumentResponse] = []
    user_role: Optional[str] = None # OWNER, EDITOR, COLLABORATOR, VIEWER, PURCHASER

    class Config:
        from_attributes = True

class MissionPublicSanitizedResponse(BaseModel):
    """
    CRITICAL SECURITY SCHEMA:
    When a Mission is listed on the marketplace or publicly discovered by a non-purchaser,
    sensitive findings, lessons learned, formulas, technical details and confidential documents
    are strictly redacted server-side.
    """
    id: UUID
    continuum_id: str
    heading: str
    problem_statement: Optional[str] = None
    project_value_est: Decimal
    currency: str
    visibility: str
    collaboration_open: bool
    created_at: datetime
    is_protected_marketplace: bool = True
    notice: str = "Technical findings, formulas, lessons learned, and documents are cryptographically protected until authorized purchase or invitation."
