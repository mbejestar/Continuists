from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

class MarketplaceSubmitRequest(BaseModel):
    proposed_value: Decimal = Field(..., gt=0)
    asking_price: Decimal = Field(..., gt=0)
    fee_tier: str = Field("DIRECT", pattern="^(DIRECT|ASSISTED)$")
    summary_non_confidential: str = Field(..., min_length=20, max_length=1500)
    industry: str = Field(..., min_length=2, max_length=100)

class MarketplaceEvaluationRequest(BaseModel):
    # 10 Continuum evaluation dimensions (1 to 10)
    score_originality: int = Field(..., ge=1, le=10)
    score_completeness: int = Field(..., ge=1, le=10)
    score_practical_usefulness: int = Field(..., ge=1, le=10)
    score_technical_depth: int = Field(..., ge=1, le=10)
    score_supporting_evidence: int = Field(..., ge=1, le=10)
    score_uniqueness: int = Field(..., ge=1, le=10)
    score_industry_relevance: int = Field(..., ge=1, le=10)
    score_market_relevance: int = Field(..., ge=1, le=10)
    score_ownership_rights: int = Field(..., ge=1, le=10)
    score_documentation_quality: int = Field(..., ge=1, le=10)
    evaluation_notes: str = Field(..., min_length=10)
    decision: str = Field(..., pattern="^(APPROVED|REJECTED|ADDITIONAL_INFORMATION_REQUIRED)$")

class MarketplaceListingResponse(BaseModel):
    id: UUID
    mission_id: UUID
    seller_id: UUID
    proposed_value: Decimal
    asking_price: Decimal
    currency: str
    fee_tier: str
    status: str
    summary_non_confidential: str
    industry: str
    mission_heading: Optional[str] = None
    problem_statement: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PurchaseRequest(BaseModel):
    license_type: str = Field(
        "ACCESS_LICENCE",
        pattern="^(ACCESS_LICENCE|LIMITED_USE_LICENCE|ASSIGNMENT_OF_SPECIFIED_RIGHTS)$"
    )
    terms_confirmed: bool = Field(True, description="Must confirm legal purchase and license agreement")

class PurchaseResponse(BaseModel):
    id: UUID
    listing_id: UUID
    mission_id: UUID
    buyer_id: UUID
    seller_id: UUID
    gross_amount: Decimal
    platform_fee_amount: Decimal
    platform_fee_rate: Decimal
    seller_net_amount: Decimal
    currency: str
    fee_tier: str
    license_type: str
    payment_reference: str
    payment_status: str
    created_at: datetime

    class Config:
        from_attributes = True
