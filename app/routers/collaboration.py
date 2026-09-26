from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.collaboration import MissionCollaborator, CollaborationRequest
from backend.app.models.message import Notification
from backend.app.schemas.collaboration import (
    CollaborationRequestCreate,
    InviteCollaboratorRequest,
    CollaborationResponse,
    CollaboratorMemberResponse
)

router = APIRouter(tags=["Collaboration"])

@router.post("/missions/{mission_id}/collaboration-requests", response_model=CollaborationResponse)
async def request_collaboration(
    mission_id: UUID,
    payload: CollaborationRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Users can request collaboration only when a Mission is PUBLIC.
    For PRIVATE Missions, owner must explicitly invite the person.
    """
    stmt = select(Mission).where(Mission.id == mission_id)
    res = await db.execute(stmt)
    mission = res.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    if mission.visibility != "PUBLIC":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot request collaboration on a PRIVATE Mission. You must receive an explicit invitation from the owner."
        )

    if mission.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are the owner of this mission.")

    # Check already collaborator
    collab_stmt = select(MissionCollaborator).where(
        and_(MissionCollaborator.mission_id == mission_id, MissionCollaborator.user_id == current_user.id)
    )
    if (await db.execute(collab_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are already a collaborator on this mission.")

    collab_req = CollaborationRequest(
        mission_id=mission.id,
        requester_id=current_user.id,
        message=payload.message,
        status="PENDING"
    )
    db.add(collab_req)

    # Notify mission owner
    notif = Notification(
        user_id=mission.owner_id,
        title="New Collaboration Request",
        message=f"{current_user.first_name} {current_user.last_name} ({current_user.continuum_id}) requested to collaborate on '{mission.heading}'.",
        notification_type="COLLABORATION_REQUEST",
        reference_type="MISSION",
        reference_id=mission.id
    )
    db.add(notif)
    await db.commit()
    await db.refresh(collab_req)

    return collab_req


@router.post("/collaboration-requests/{request_id}/accept")
async def accept_collaboration_request(
    request_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CollaborationRequest).join(Mission).where(CollaborationRequest.id == request_id)
    res = await db.execute(stmt)
    collab_req = res.scalar_one_or_none()

    if not collab_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    # Check mission owner
    mission = (await db.execute(select(Mission).where(Mission.id == collab_req.mission_id))).scalar_one()
    if mission.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only mission owner can accept requests.")

    collab_req.status = "ACCEPTED"
    collab_req.reviewed_by = current_user.id
    collab_req.reviewed_at = datetime.now(timezone.utc)

    # Add collaborator
    new_collab = MissionCollaborator(
        mission_id=mission.id,
        user_id=collab_req.requester_id,
        role="COLLABORATOR",
        invited_by=current_user.id
    )
    db.add(new_collab)

    notif = Notification(
        user_id=collab_req.requester_id,
        title="Collaboration Accepted",
        message=f"You have been accepted as a collaborator on Mission '{mission.heading}'.",
        notification_type="COLLABORATION_ACCEPTED",
        reference_type="MISSION",
        reference_id=mission.id
    )
    db.add(notif)
    await db.commit()

    await log_audit_event(
        db=db,
        action=AuditAction.COLLABORATION_ACCEPTED,
        entity="COLLABORATION",
        user_id=current_user.id,
        entity_id=collab_req.id,
        request=request
    )

    return {"message": "Collaboration request accepted. Access granted."}


@router.post("/collaboration-requests/{request_id}/decline")
async def decline_collaboration_request(
    request_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CollaborationRequest).where(CollaborationRequest.id == request_id)
    res = await db.execute(stmt)
    collab_req = res.scalar_one_or_none()

    if not collab_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    collab_req.status = "DECLINED"
    collab_req.reviewed_by = current_user.id
    collab_req.reviewed_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "Collaboration request declined."}


@router.post("/missions/{mission_id}/invite")
async def invite_collaborator(
    mission_id: UUID,
    payload: InviteCollaboratorRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Explicit invitation by owner (works for both PRIVATE and PUBLIC missions)."""
    stmt = select(Mission).where(and_(Mission.id == mission_id, Mission.owner_id == current_user.id))
    mission = (await db.execute(stmt)).scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found or not owner.")

    # Find target user by Continuum ID or email
    target_q = payload.user_continuum_id_or_email.strip()
    target_user = (await db.execute(
        select(User).where(or_(User.continuum_id == target_q.upper(), User.email == target_q.lower()))
    )).scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found with provided Continuum ID or email.")

    new_collab = MissionCollaborator(
        mission_id=mission.id,
        user_id=target_user.id,
        role=payload.role,
        invited_by=current_user.id
    )
    db.add(new_collab)
    await db.commit()

    await log_audit_event(
        db=db,
        action=AuditAction.COLLABORATOR_INVITED,
        entity="MISSION",
        user_id=current_user.id,
        entity_id=mission.id,
        metadata_json={"target_user_id": str(target_user.id), "role": payload.role},
        request=request
    )

    return {"message": f"Successfully invited {target_user.first_name} as {payload.role}."}
