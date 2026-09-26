from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditLog

class AuditAction:
    USER_CREATED_MISSION = "USER_CREATED_MISSION"
    MISSION_UPDATED = "MISSION_UPDATED"
    MISSION_MADE_PUBLIC = "MISSION_MADE_PUBLIC"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    COLLABORATOR_INVITED = "COLLABORATOR_INVITED"
    COLLABORATION_ACCEPTED = "COLLABORATION_ACCEPTED"
    COLLABORATION_DECLINED = "COLLABORATION_DECLINED"
    MISSION_SUBMITTED_FOR_SALE = "MISSION_SUBMITTED_FOR_SALE"
    MISSION_APPROVED = "MISSION_APPROVED"
    MISSION_REJECTED = "MISSION_REJECTED"
    MISSION_PURCHASED = "MISSION_PURCHASED"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_REVOKED = "ACCESS_REVOKED"
    TERMS_ACCEPTED = "TERMS_ACCEPTED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    INACTIVITY_RULE_UPDATED = "INACTIVITY_RULE_UPDATED"
    SUCCESSOR_NOMINATED = "SUCCESSOR_NOMINATED"
    DATA_EXPORT_REQUESTED = "DATA_EXPORT_REQUESTED"
    ACCOUNT_DEACTIVATED = "ACCOUNT_DEACTIVATED"

async def log_audit_event(
    db: AsyncSession,
    action: str,
    entity: str,
    user_id: Optional[UUID] = None,
    entity_id: Optional[UUID] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Persists an immutable audit log entry for security and regulatory compliance (POPIA).
    Extracts IP address and User-Agent if request is provided.
    """
    ip_address = None
    user_agent = None

    if request:
        client = request.client
        ip_address = client.host if client else None
        user_agent = request.headers.get("user-agent")

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        metadata_json=metadata_json or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    return log_entry
