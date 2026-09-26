from datetime import datetime, timezone
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.legal import MissionOwnershipDeclaration, LegalAgreement, UserAgreement
from backend.app.schemas.legal import (
    OwnershipDeclarationRequest,
    OwnershipDeclarationResponse,
    LegalAgreementResponse,
    UserAgreementAcceptance
)

router = APIRouter(tags=["Legal & Declarations"])

@router.post("/missions/{mission_id}/ownership-declaration", response_model=OwnershipDeclarationResponse, status_code=status.HTTP_201_CREATED)
async def declare_mission_ownership(
    mission_id: UUID,
    payload: OwnershipDeclarationRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submits mandatory Ownership Declaration before marketplace submission:
    - Did you create this work yourself?
    - Were other people involved?
    - Was the work created during employment?
    - Was it created for a client?
    - Does another organisation own rights in this material?
    - Does the Mission contain confidential information?
    - Does the Mission contain third-party material?
    - Confirmation of rights and permissions.
    """
    stmt = select(Mission).where(and_(Mission.id == mission_id, Mission.owner_id == current_user.id))
    mission = (await db.execute(stmt)).scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found or not owner.")

    existing_stmt = select(MissionOwnershipDeclaration).where(MissionOwnershipDeclaration.mission_id == mission_id)
    decl = (await db.execute(existing_stmt)).scalar_one_or_none()

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not decl:
        decl = MissionOwnershipDeclaration(
            mission_id=mission.id,
            user_id=current_user.id,
            created_myself=payload.created_myself,
            others_involved=payload.others_involved,
            created_during_employment=payload.created_during_employment,
            created_for_client=payload.created_for_client,
            org_owns_rights=payload.org_owns_rights,
            contains_confidential_info=payload.contains_confidential_info,
            contains_third_party_material=payload.contains_third_party_material,
            full_legal_declaration_confirmed=payload.full_legal_declaration_confirmed,
            declaration_text=payload.declaration_text,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(decl)
    else:
        decl.created_myself = payload.created_myself
        decl.others_involved = payload.others_involved
        decl.created_during_employment = payload.created_during_employment
        decl.created_for_client = payload.created_for_client
        decl.org_owns_rights = payload.org_owns_rights
        decl.contains_confidential_info = payload.contains_confidential_info
        decl.contains_third_party_material = payload.contains_third_party_material
        decl.full_legal_declaration_confirmed = payload.full_legal_declaration_confirmed
        decl.declaration_text = payload.declaration_text
        decl.ip_address = ip_address
        decl.user_agent = user_agent
        decl.declared_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(decl)

    await log_audit_event(
        db=db,
        action="OWNERSHIP_DECLARED",
        entity="MISSION_OWNERSHIP_DECLARATION",
        user_id=current_user.id,
        entity_id=decl.id,
        metadata_json={"mission_id": str(mission_id)},
        request=request
    )

    return decl


@router.get("/missions/{mission_id}/ownership-declaration", response_model=OwnershipDeclarationResponse)
async def get_ownership_declaration(
    mission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MissionOwnershipDeclaration).join(Mission).where(
        and_(MissionOwnershipDeclaration.mission_id == mission_id, Mission.owner_id == current_user.id)
    )
    res = await db.execute(stmt)
    decl = res.scalar_one_or_none()
    if not decl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ownership declaration not found for this mission.")
    return decl


@router.get("/legal/agreements", response_model=List[LegalAgreementResponse])
async def list_legal_agreements(db: AsyncSession = Depends(get_db)):
    """Lists current active legal terms (POPIA, Terms of Service, Marketplace Agreement, License)."""
    stmt = select(LegalAgreement).where(LegalAgreement.is_active == True)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/legal/accept")
async def accept_legal_agreement(
    payload: UserAgreementAcceptance,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Records verifiable consent to versioned legal agreement with timestamp and IP."""
    ip_addr = request.client.host if request.client else None
    u_agent = request.headers.get("user-agent")

    user_ag = UserAgreement(
        user_id=current_user.id,
        agreement_id=payload.agreement_id,
        agreement_version=payload.agreement_version,
        ip_address=ip_addr,
        user_agent=u_agent
    )
    db.add(user_ag)
    await db.commit()

    await log_audit_event(
        db=db,
        action=AuditAction.TERMS_ACCEPTED,
        entity="LEGAL_AGREEMENT",
        user_id=current_user.id,
        entity_id=payload.agreement_id,
        metadata_json={"version": payload.agreement_version},
        request=request
    )

    return {"message": "Legal agreement accepted and logged."}
