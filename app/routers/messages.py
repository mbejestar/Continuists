from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.models.user import User
from backend.app.models.message import Message, Notification
from backend.app.schemas.message import MessageCreate, MessageResponse

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.get("", response_model=List[MessageResponse])
async def list_messages(
    mission_id: Optional[UUID] = None,
    with_user_continuum_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves user messages.
    Security: Do not expose private conversations to unauthorized users.
    """
    stmt = select(Message).where(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    )

    if mission_id:
        stmt = stmt.where(Message.mission_id == mission_id)

    if with_user_continuum_id:
        target_user = (await db.execute(select(User).where(User.continuum_id == with_user_continuum_id.upper()))).scalar_one_or_none()
        if target_user:
            stmt = stmt.where(
                or_(
                    and_(Message.sender_id == current_user.id, Message.recipient_id == target_user.id),
                    and_(Message.sender_id == target_user.id, Message.recipient_id == current_user.id)
                )
            )

    stmt = stmt.order_by(Message.created_at.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sends a context-linked direct message to another user."""
    target_user = (await db.execute(select(User).where(User.continuum_id == payload.recipient_continuum_id.upper().strip()))).scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient user not found.")

    new_msg = Message(
        sender_id=current_user.id,
        recipient_id=target_user.id,
        mission_id=payload.mission_id,
        content=payload.content.strip(),
        is_read=False
    )
    db.add(new_msg)

    # In-app notification
    notif = Notification(
        user_id=target_user.id,
        title=f"New Message from {current_user.first_name}",
        message=f"{current_user.first_name}: {payload.content[:80]}...",
        notification_type="NEW_MESSAGE",
        reference_type="MESSAGE",
        reference_id=new_msg.id
    )
    db.add(notif)

    await db.commit()
    await db.refresh(new_msg)
    return new_msg


@router.patch("/{message_id}/read")
async def mark_message_as_read(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Message).where(and_(Message.id == message_id, Message.recipient_id == current_user.id))
    msg = (await db.execute(stmt)).scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not recipient.")

    msg.is_read = True
    msg.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Message marked as read."}
