from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.core.payment import get_payment_gateway
from backend.app.core.biometric import get_biometric_service
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User, UserSettings
from backend.app.schemas.user import UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    settings_obj = (await db.execute(stmt)).scalar_one_or_none()
    if not settings_obj:
        settings_obj = UserSettings(user_id=current_user.id, dark_mode=False)
        db.add(settings_obj)
        await db.commit()
        await db.refresh(settings_obj)
    return settings_obj


@router.patch("", response_model=UserSettingsResponse)
async def update_settings(
    payload: UserSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates user settings.
    LOCATION REQUIREMENT:
    Dark Mode toggle is strictly modified here (Profile -> Settings -> Appearance -> Dark Mode).
    """
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    settings_obj = (await db.execute(stmt)).scalar_one_or_none()
    if not settings_obj:
        settings_obj = UserSettings(user_id=current_user.id)
        db.add(settings_obj)

    if payload.dark_mode is not None:
        settings_obj.dark_mode = payload.dark_mode
    if payload.email_notifications is not None:
        settings_obj.email_notifications = payload.email_notifications
    if payload.release_reminder_days is not None:
        settings_obj.release_reminder_days = payload.release_reminder_days
    if payload.biometric_recovery_enabled is not None:
        settings_obj.biometric_recovery_enabled = payload.biometric_recovery_enabled

    await db.commit()
    await db.refresh(settings_obj)

    await log_audit_event(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        entity="USER_SETTINGS",
        user_id=current_user.id,
        entity_id=settings_obj.id,
        metadata_json={"dark_mode": settings_obj.dark_mode, "biometric": settings_obj.biometric_recovery_enabled},
        request=request
    )

    return settings_obj


@router.post("/premium/upgrade")
async def upgrade_to_premium(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upgrades user account to CONTINUUM PREMIUM:
    - R100 per month
    - Unlocks unlimited mission document storage (exceeding 50MB free quota)
    - Unlocks advanced succession and marketplace priority
    """
    if current_user.subscription == "PREMIUM":
        return {"message": "You are already a Continuum Premium subscriber.", "subscription": "PREMIUM"}

    payment_service = get_payment_gateway()
    sub_res = await payment_service.create_premium_subscription(
        user_id=str(current_user.id),
        user_email=current_user.email,
        monthly_amount=Decimal("100.00")
    )

    current_user.subscription = "PREMIUM"
    current_user.subscription_renews_at = datetime.now(timezone.utc) + timedelta(days=30)
    await db.commit()

    await log_audit_event(
        db=db,
        action="USER_UPGRADED_PREMIUM",
        entity="SUBSCRIPTION",
        user_id=current_user.id,
        entity_id=current_user.id,
        metadata_json={"amount": "R100.00", "provider": "Paystack"},
        request=request
    )

    return {
        "message": "Successfully upgraded to Continuum Premium (R100/mo). Mission document limits unlocked.",
        "subscription": "PREMIUM",
        "subscription_renews_at": current_user.subscription_renews_at
    }
