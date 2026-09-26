"""
Continuum Mission Lifecycle & Preservation Endpoints.

Core Domain Rules:
-----------------
1. PRIVATE BY DEFAULT:
   Every new Mission is initialized as PRIVATE. It cannot be discovered
   in the public catalog until the owner explicitly executes the /publish action.

2. OPTIONAL MANUAL TYPING:
   Technical, chemical, and engineering creators frequently possess existing
   specifications, formulas, and CAD drawings. Manual typing is NEVER mandatory;
   a creator may provide only a heading and attach supporting documentation.

3. ASYMMETRIC REDACTION:
   Public missions expose only non-confidential headings, problem statements,
   and broad valuations. All proprietary findings, lessons learned, and documents
   are redacted on the backend for non-purchasers.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.core.security import generate_mission_continuum_id
from backend.app.core.permissions import (
    get_current_user,
    get_current_user_optional,
    evaluate_mission_clearance,
    MissionRole,
    sanitize_mission_for_public_viewer
)
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.document import MissionDocument
from backend.app.models.collaboration import MissionCollaborator
from backend.app.models.succession import MissionReleaseRule, MissionSuccessor
from backend.app.schemas.mission import (
    MissionCreate,
    MissionUpdate,
    MissionDetailResponse,
    MissionPublicSanitizedResponse
)

router = APIRouter(prefix="/missions", tags=["Missions"])

@router.post("", response_model=MissionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new Mission in the knowledge vault.
    
    Guarantees:
    - Automatically generates high-entropy public Continuum ID (e.g. MSN-4B82-9Q1Z).
    - Forces PRIVATE visibility by default.
    - Permits creation without manual problem/findings fields (document-first workflow).
    - Binds initial inactivity timers and succession nominees.
    """
    mission_cnt_id = generate_mission_continuum_id()

    new_mission = Mission(
        continuum_id=mission_cnt_id,
        owner_id=current_user.id,
        heading=payload.heading.strip(),
        problem_statement=payload.problem_statement.strip() if payload.problem_statement else None,
        what_we_found=payload.what_we_found.strip() if payload.what_we_found else None,
        lessons_learned=payload.lessons_learned.strip() if payload.lessons_learned else None,
        project_value_est=payload.project_value_est,
        currency="ZAR",
        amount_spent=payload.amount_spent,
        visibility="PRIVATE",  # Strictly PRIVATE by default
        collaboration_open=payload.collaboration_open,
        is_archived=False,
        last_activity_at=datetime.now(timezone.utc)
    )
    db.add(new_mission)
    await db.flush()

    # 10. Inactivity release settings
    if payload.release_rule:
        release_rule = MissionReleaseRule(
            mission_id=new_mission.id,
            inactivity_period_value=payload.release_rule.inactivity_period_value,
            inactivity_period_unit=payload.release_rule.inactivity_period_unit,
            is_enabled=payload.release_rule.is_enabled,
            last_activity_reset_at=datetime.now(timezone.utc)
        )
        db.add(release_rule)

    # 11. Succession planning
    if payload.successor:
        successor = MissionSuccessor(
            mission_id=new_mission.id,
            user_id=current_user.id,
            name=payload.successor.name.strip(),
            relationship=payload.successor.relationship.strip(),
            phone=payload.successor.phone.strip(),
            email=payload.successor.email.lower().strip(),
            alternative_contact=payload.successor.alternative_contact.strip() if payload.successor.alternative_contact else None,
            intended_action=payload.successor.intended_action,
            legal_notice_acknowledged=True
        )
        db.add(successor)

    await db.commit()
    await db.refresh(new_mission)

    await log_audit_event(
        db=db,
        action=AuditAction.USER_CREATED_MISSION,
        entity="MISSION",
        user_id=current_user.id,
        entity_id=new_mission.id,
        metadata_json={
            "continuum_id": new_mission.continuum_id,
            "heading": new_mission.heading,
            "visibility": "PRIVATE"
        },
        request=request
    )

    new_mission.documents = []
    new_mission.user_role = MissionRole.OWNER
    return new_mission


@router.get("", response_model=List[MissionDetailResponse])
async def list_user_accessible_missions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the complete directory of missions owned by the user,
    or where the user holds an active collaborator or purchaser clearance.
    """
    # 1. Owned missions
    owned_stmt = select(Mission).options(selectinload(Mission.documents)).where(
        and_(Mission.owner_id == current_user.id, Mission.is_archived == False)
    ).order_by(Mission.last_activity_at.desc())
    owned_missions = list((await db.execute(owned_stmt)).scalars().all())

    # 2. Collaborator missions
    collab_stmt = select(Mission).join(MissionCollaborator).options(selectinload(Mission.documents)).where(
        MissionCollaborator.user_id == current_user.id
    )
    collab_missions = (await db.execute(collab_stmt)).scalars().all()
    
    seen_ids = {m.id for m in owned_missions}
    for m in collab_missions:
        if m.id not in seen_ids:
            owned_missions.append(m)
            seen_ids.add(m.id)

    for m in owned_missions:
        m.user_role = MissionRole.OWNER if m.owner_id == current_user.id else MissionRole.COLLABORATOR

    return owned_missions


@router.get("/{mission_id}")
async def get_mission_by_id(
    mission_id: UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches a Mission record by UUID.
    
    CRITICAL SECURITY CHECK:
    - If user has full clearance (Owner, Active Collaborator, Purchaser): returns
      unmasked findings, lessons, calculations, and document registry.
    - If mission is PUBLIC and requester is a prospective buyer: returns
      sanitized redaction view.
    - If mission is PRIVATE and requester is unauthorized: returns HTTP 404 to
      prevent ID enumeration.
    """
    stmt = select(Mission).options(selectinload(Mission.documents)).where(Mission.id == mission_id)
    mission = (await db.execute(stmt)).scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found in vault.")

    role, has_full_clearance = await evaluate_mission_clearance(mission, current_user, db)

    if has_full_clearance:
        mission.user_role = role
        return mission

    # Non-cleared user inspecting a PUBLIC mission -> sanitize server-side!
    if mission.visibility == "PUBLIC":
        return sanitize_mission_for_public_viewer(mission)

    # PRIVATE mission without clearance -> deny existence
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Mission not found or you lack authorized clearance to inspect private archives."
    )


@router.post("/{mission_id}/publish")
async def publish_mission(
    mission_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Promotes a private Mission to PUBLIC status for discovery and marketplace submission."""
    stmt = select(Mission).where(and_(Mission.id == mission_id, Mission.owner_id == current_user.id))
    mission = (await db.execute(stmt)).scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found or you are not the owner.")

    mission.visibility = "PUBLIC"
    mission.last_activity_at = datetime.now(timezone.utc)
    await db.commit()

    await log_audit_event(
        db=db,
        action=AuditAction.MISSION_MADE_PUBLIC,
        entity="MISSION",
        user_id=current_user.id,
        entity_id=mission.id,
        metadata_json={"continuum_id": mission.continuum_id},
        request=request
    )

    return {"message": f"Mission '{mission.heading}' is now PUBLIC. Sensitive findings remain protected.", "visibility": "PUBLIC"}
