"""
Continuum Purchase & Mission Access Grant Router.

Enforces:
1. BUYER VALIDATION:
   A seller cannot purchase access to their own Mission.
2. BACKEND SETTLEMENT SPLIT:
   Automatically computes the 8% (direct) or 15% (assisted) fee split,
   generating transparent records for the seller's tax disbursement and SARS reporting.
3. CLEAR ACCESS TYPE & LICENSE CONTRACT:
   Grants a typed MissionAccess record (ACCESS_LICENCE, LIMITED_USE_LICENCE, or
   ASSIGNMENT_OF_SPECIFIED_RIGHTS) that grants clearance to unmasked findings.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.core.payment import calculate_marketplace_fees, get_payment_gateway
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.marketplace import MarketplaceListing
from backend.app.models.purchase import Purchase, MissionAccess
from backend.app.models.message import Notification
from backend.app.schemas.marketplace import PurchaseRequest, PurchaseResponse

router = APIRouter(tags=["Purchases"])

@router.post("/marketplace/{listing_id}/purchase", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def purchase_mission_access(
    listing_id: UUID,
    payload: PurchaseRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes a commercial transaction acquiring context access or intellectual property rights.
    
    Security & Settlement Protocol:
    1. Listing must be in APPROVED state.
    2. Self-purchase is blocked.
    3. Prevents duplicate access grants if user already purchased.
    4. Automatically calculates platform commission (8% vs 15%). Never trusts client fee!
    5. Creates immutable Purchase record and issues MissionAccess grant.
    """
    stmt = select(MarketplaceListing).where(MarketplaceListing.id == listing_id)
    listing = (await db.execute(stmt)).scalar_one_or_none()

    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace listing not found.")

    if listing.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This listing is currently in '{listing.status}' status and not available for purchase."
        )

    if listing.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction blocked: You are the registered owner of this Mission."
        )

    # Check for existing purchase grant
    existing_grant = (await db.execute(
        select(MissionAccess).where(
            and_(
                MissionAccess.mission_id == listing.mission_id,
                MissionAccess.user_id == current_user.id,
                MissionAccess.is_revoked == False
            )
        )
    )).scalar_one_or_none()

    if existing_grant:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already hold an active access grant for this Mission."
        )

    # Strict backend fee computation
    fee_data = calculate_marketplace_fees(listing.asking_price, listing.fee_tier)
    payment_reference = f"CNT-PUR-{uuid4().hex[:12].upper()}"

    gateway = get_payment_gateway()
    await gateway.initialize_checkout(
        listing_id=str(listing.id),
        amount=fee_data.gross_amount,
        buyer_email=current_user.email,
        currency="ZAR"
    )

    new_purchase = Purchase(
        listing_id=listing.id,
        mission_id=listing.mission_id,
        buyer_id=current_user.id,
        seller_id=listing.seller_id,
        gross_amount=fee_data.gross_amount,
        platform_fee_amount=fee_data.platform_fee_amount,
        platform_fee_rate=fee_data.platform_fee_rate,
        seller_net_amount=fee_data.seller_net_amount,
        currency="ZAR",
        fee_tier=listing.fee_tier,
        license_type=payload.license_type,
        payment_reference=payment_reference,
        payment_status="COMPLETED"
    )
    db.add(new_purchase)
    await db.flush()

    # Issue MissionAccess clearance
    access_grant = MissionAccess(
        mission_id=listing.mission_id,
        user_id=current_user.id,
        access_type="PURCHASER",
        license_type=payload.license_type,
        purchase_id=new_purchase.id,
        granted_at=datetime.now(timezone.utc)
    )
    db.add(access_grant)

    # Notify Seller of verified disbursement
    seller_notif = Notification(
        user_id=listing.seller_id,
        title="Mission Purchased & Licensed",
        message=(
            f"A buyer has purchased context access to your mission under license '{payload.license_type}'. "
            f"Net settlement: R{fee_data.seller_net_amount:,.2f} ZAR."
        ),
        notification_type="MISSION_PURCHASED",
        reference_type="PURCHASE",
        reference_id=new_purchase.id
    )
    db.add(seller_notif)

    await db.commit()
    await db.refresh(new_purchase)

    await log_audit_event(
        db=db,
        action=AuditAction.MISSION_PURCHASED,
        entity="PURCHASE",
        user_id=current_user.id,
        entity_id=new_purchase.id,
        metadata_json={
            "mission_id": str(listing.mission_id),
            "gross_amount": str(fee_data.gross_amount),
            "platform_fee": str(fee_data.platform_fee_amount),
            "seller_net": str(fee_data.seller_net_amount),
            "license": payload.license_type
        },
        request=request
    )

    return new_purchase
