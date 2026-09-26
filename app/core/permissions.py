"""
Continuum Access Control & Server-Side Redaction Engine.

Design Principles & Threat Model:
---------------------------------
1. ZERO CLIENT-SIDE TRUST:
   A user can modify local JavaScript, manipulate local state, or issue
   raw curl requests directly against /api endpoints. Therefore, under no
   circumstances does the API return 'what_we_found', 'lessons_learned',
   or document download URLs to an unpurchased prospective buyer.

2. ASYMMETRIC VISIBILITY MODEL:
   - PRIVATE: Completely hidden. Only owner and explicitly invited collaborators
     even know the mission exists.
   - PUBLIC: Discoverable in catalog and search, but findings, mathematical models,
     chemical formulas, engineering drawings, and source code are cryptographically
     sealed until a transaction completes and an access grant is issued.

3. ROLE HIERARCHY:
   OWNER > EDITOR > COLLABORATOR > PURCHASER > VIEWER > ANONYMOUS
"""

from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.core.database import get_db
from backend.app.core.security import decode_token
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.collaboration import MissionCollaborator
from backend.app.models.purchase import MissionAccess

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

class MissionRole:
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    COLLABORATOR = "COLLABORATOR"
    PURCHASER = "PURCHASER"
    VIEWER = "VIEWER"
    PUBLIC_VISITOR = "PUBLIC_VISITOR"
    UNAUTHORIZED = "UNAUTHORIZED"


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Safely retrieves the current user if a valid bearer token was presented.
    Returns None for unauthenticated public catalog visitors.
    """
    if not token:
        return None
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        return None
    try:
        user_uuid = UUID(payload["sub"])
    except (ValueError, TypeError):
        return None

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user and not user.is_active:
        return None
    return user


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Strict dependency for endpoints requiring authenticated active user credentials."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid Continuum session token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def evaluate_mission_clearance(
    mission: Mission,
    user: Optional[User],
    db: AsyncSession
) -> Tuple[str, bool]:
    """
    Determines the highest clearance role and whether the user is authorized
    to view unmasked proprietary context (findings, lessons learned, documents).

    Returns:
        (effective_role: str, has_full_clearance: bool)
    """
    if not user:
        return (MissionRole.PUBLIC_VISITOR, False)

    # 1. Mission Creator / Owner has unconditional authority
    if mission.owner_id == user.id:
        return (MissionRole.OWNER, True)

    # 2. Check explicitly invited collaborators
    collab_stmt = select(MissionCollaborator).where(
        and_(
            MissionCollaborator.mission_id == mission.id,
            MissionCollaborator.user_id == user.id
        )
    )
    collab = (await db.execute(collab_stmt)).scalar_one_or_none()
    if collab:
        # Collaborators, Editors, and Viewers can inspect context
        return (collab.role, True)

    # 3. Check verified purchases (Marketplace access grant)
    access_stmt = select(MissionAccess).where(
        and_(
            MissionAccess.mission_id == mission.id,
            MissionAccess.user_id == user.id,
            MissionAccess.is_revoked == False
        )
    )
    access_grant = (await db.execute(access_stmt)).scalar_one_or_none()
    if access_grant:
        return (MissionRole.PURCHASER, True)

    return (MissionRole.PUBLIC_VISITOR, False)


def sanitize_mission_for_public_viewer(mission: Mission) -> Dict[str, Any]:
    """
    CRITICAL SERVER-SIDE REDACTION LAYER:
    Generates a sanitized projection for prospective buyers or public discovery.
    
    GUARANTEES:
    - 'what_we_found' is strictly set to None.
    - 'lessons_learned' is strictly set to None.
    - 'documents' array is emptied, preventing document metadata, hashes,
      or storage paths from leaking before financial commitment.
    - Sets 'is_protected_marketplace: True' with statutory warning.
    """
    return {
        "id": mission.id,
        "continuum_id": mission.continuum_id,
        "heading": mission.heading,
        "problem_statement": mission.problem_statement,
        "what_we_found": None,  # REDACTED AT SERVING TIME
        "lessons_learned": None, # REDACTED AT SERVING TIME
        "project_value_est": mission.project_value_est,
        "currency": mission.currency,
        "amount_spent": mission.amount_spent,
        "visibility": mission.visibility,
        "collaboration_open": mission.collaboration_open,
        "is_archived": mission.is_archived,
        "created_at": mission.created_at,
        "updated_at": mission.updated_at,
        "documents": [],  # REDACTED: Zero document records returned
        "is_protected_marketplace": True,
        "clearance_level": MissionRole.PUBLIC_VISITOR,
        "protection_notice": (
            "Proprietary findings, calculations, lessons learned, and documents "
            "are sealed under Continuum Trust Protocol. Complete an authorized "
            "license purchase or request owner collaboration to access."
        )
    }
