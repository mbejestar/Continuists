from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.models.user import User
from backend.app.models.message import Notification
from backend.app.schemas.message import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves all notifications for current user."""
    stmt = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Notification).where(and_(Notification.id == notification_id, Notification.user_id == current_user.id))
    notif = (await db.execute(stmt)).scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_read = True
    await db.commit()
    return {"message": "Notification marked as read."}
