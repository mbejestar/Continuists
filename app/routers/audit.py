from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.models.user import User
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

class AuditLogResponse(BaseModel):
    id: UUID
    action: str
    entity: str
    entity_id: UUID = None
    created_at: datetime
    metadata_json: dict = {}

    class Config:
        from_attributes = True

@router.get("", response_model=List[AuditLogResponse])
async def get_my_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns immutable audit logs for the authenticated user (POPIA transparency).
    """
    stmt = select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(AuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
