"""
Continuum Marketplace & Institutional Valuation Router.

Enforces:
1. MANDATORY OWNERSHIP DECLARATION:
   A user cannot list a mission on the marketplace without formal, timestamped
   declarations certifying that they created the work, that no employer holds
   statutory copyright under the SA Copyright Act 98 of 1978, and that the material
   does not violate client non-disclosure agreements.

2. TEN-DIMENSION CONTINUUM EVALUATION:
   Users cannot assign arbitrary valuation and immediately list; every submission
   passes through formal scoring:
   - Originality, Completeness, Practical Usefulness, Technical Depth,
     Supporting Evidence, Uniqueness, Industry Relevance, Market Relevance,
     Ownership Rights, Documentation Quality.

3. DIRECT VS ASSISTED COMMISSIONS:
   Automated 8% (direct buyer discovery) vs 15% (Continuum syndicated introduction)
   calculated strictly on the backend.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user, get_current_user_optional, evaluate_mission_clearance, MissionRole
from backend.app.core.payment import calculate_marketplace_fees
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.marketplace import MarketplaceListing, MarketplaceEvaluation
from backend.app.models.legal import MissionOwnershipDeclaration
from backend.app.schemas.marketplace import (
    MarketplaceSubmitRequest,
    MarketplaceEvaluationRequest,
    MarketplaceListingResponse
)

router = APIRouter(tags=["Marketplace"])

@router.post("/missions/{mission_id}/marketplace", response_model=MarketplaceListingResponse, status_code=status.HTTP_201_CREATED)
async def submit_mission_for_marketplace(
    mission_id: UUID,
    payload: MarketplaceSubmitRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an eligible Mission for sale on the Continuum marketplace.
    
    STATUTORY PRE-CONDITIONS:
    1. Caller must be the verified Mission Owner.
    2. Owner must have executed the formal 7-point Ownership & Non-Infringement Declaration.
    3. Status is initialized to SUBMITTED and queued for evaluation review.
    """
    stmt = select(Mission).where(and_(Mission.id == mission_id, Mission.owner_id == current_user.id))
    mission = (await db.execute(stmt)).scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found or you are not the registered owner.")

    # Verify immutable ownership declaration
    decl_stmt = select(MissionOwnershipDeclaration).where(MissionOwnershipDeclaration.mission_id == mission_id)
    decl = (await db.execute(decl_stmt)).scalar_one_or_none()
    if not decl or not decl.full_legal_declaration_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Marketplace listing rejected: Statutory Ownership Declaration missing. "
                "You must formally execute the 7-point declaration verifying independent copyright, "
                "employer non-infringement, and client confidentiality clearance."
            )
        )

    # Check existing submission
    existing_stmt = select(MarketplaceListing).where(MarketplaceListing.mission_id == mission_id)
    if (await db.execute(existing_stmt)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Mission is already active in the evaluation or listing pipeline."
        )

    new_listing = MarketplaceListing(
        mission_id=mission.id,
        seller_id=current_user.id,
        proposed_value=payload.proposed_value,
        asking_price=payload.asking_price,
        currency="ZAR",
        fee_tier=payload.fee_tier,
        status="SUBMITTED", # Enters evaluation pipeline
        summary_non_confidential=payload.summary_non_confidential.strip(),
        industry=payload.industry.strip()
    )
    db.add(new_listing)
    await db.commit()
    await db.refresh(new_listing)

    await log_audit_event(
        db=db,
        action=AuditAction.MISSION_SUBMITTED_FOR_SALE,
        entity="MARKETPLACE_LISTING",
        user_id=current_user.id,
        entity_id=new_listing.id,
        metadata_json={
            "asking_price": str(payload.asking_price),
            "fee_tier": payload.fee_tier,
            "industry": payload.industry
        },
        request=request
    )

    new_listing.mission_heading = mission.heading
    new_listing.problem_statement = mission.problem_statement
    return new_listing


@router.get("/marketplace", response_model=List[MarketplaceListingResponse])
async def list_approved_marketplace_catalog(
    industry: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Public Marketplace catalog.
    
    SECURITY GUARANTEE:
    Returns ONLY APPROVED listings with strictly non-confidential summaries
    and high-level problem statements. Proprietary formulas, raw calculations,
    and documents are NEVER returned in this endpoint.
    """
    stmt = select(MarketplaceListing, Mission).join(Mission, MarketplaceListing.mission_id == Mission.id).where(
        MarketplaceListing.status == "APPROVED"
    ).order_by(MarketplaceListing.created_at.desc())

    if industry:
        stmt = stmt.where(MarketplaceListing.industry == industry.strip())

    records = (await db.execute(stmt)).all()

    return [
        MarketplaceListingResponse(
            id=listing.id,
            mission_id=listing.mission_id,
            seller_id=listing.seller_id,
            proposed_value=listing.proposed_value,
            asking_price=listing.asking_price,
            currency=listing.currency,
            fee_tier=listing.fee_tier,
            status=listing.status,
            summary_non_confidential=listing.summary_non_confidential,
            industry=listing.industry,
            mission_heading=mission.heading,
            problem_statement=mission.problem_statement,
            created_at=listing.created_at,
            updated_at=listing.updated_at
        ) for listing, mission in records
    ]


@router.get("/marketplace/{listing_id}/fee-preview")
async def preview_marketplace_settlement(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns automated platform fee breakdown:
    - Direct: 8% platform fee (Seller receives 92%)
    - Assisted: 15% platform fee (Seller receives 85%)
    Computed automatically with exact two-decimal ZAR precision.
    """
    stmt = select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    listing = (await db.execute(stmt)).scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace listing not found.")

    return calculate_marketplace_fees(listing.asking_price, listing.fee_tier)
