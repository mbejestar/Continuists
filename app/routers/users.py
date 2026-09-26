from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User, UserSettings
from backend.app.schemas.user import UserResponse, PublicUserProfile

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    res = await db.execute(stmt)
    current_user.settings = res.scalar_one_or_none()
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_profile(
    first_name: str = None,
    last_name: str = None,
    phone: str = None,
    province_region: str = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates user demographic information (excluding Continuum ID or email directly)."""
    if first_name:
        current_user.first_name = first_name.strip()
    if last_name:
        current_user.last_name = last_name.strip()
    if phone is not None:
        current_user.phone = phone.strip()
    if province_region:
        current_user.province_region = province_region.strip()

    await db.commit()
    await db.refresh(current_user)

    await log_audit_event(
        db=db,
        action=AuditAction.PROFILE_UPDATED,
        entity="USER",
        user_id=current_user.id,
        entity_id=current_user.id,
        metadata_json={"province_region": current_user.province_region},
        request=request
    )
    return current_user

@router.get("/{continuum_id}", response_model=PublicUserProfile)
async def get_public_user_profile(
    continuum_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public profile lookup by permanent Continuum ID.
    POPIA PRIVACY CONSTRAINT:
    Never exposes email, phone, or exact residential address to the public.
    """
    stmt = select(User).where(User.continuum_id == continuum_id.upper().strip())
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Continuum user not found.")
    return user
