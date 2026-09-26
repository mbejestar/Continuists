"""
Continuum Document Management Endpoints.

Handles:
- Streaming document upload with cryptographic SHA-256 validation
- 50MB free quota vs Unlimited Premium enforcement
- Authorized document listing and metadata inspection
- Secure deletion from both storage engine and PostgreSQL database
"""

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from backend.app.core.database import get_db
from backend.app.core.permissions import get_current_user, evaluate_mission_clearance, MissionRole
from backend.app.core.storage import get_storage_engine, process_and_validate_upload
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User
from backend.app.models.mission import Mission
from backend.app.models.document import MissionDocument
from backend.app.schemas.mission import MissionDocumentResponse

router = APIRouter(tags=["Documents"])

@router.post("/missions/{mission_id}/documents", response_model=MissionDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_mission_document(
    mission_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Attaches a technical document, drawing, or calculation archive to a Mission.
    
    Security & Integrity Pipeline:
    1. Evaluates mission edit permissions (Owner or Editor only).
    2. Computes cumulative storage currently consumed by this mission.
    3. Streams file chunks through SHA-256 hasher while verifying 50MB limit.
    4. Writes payload to object storage.
    5. Commits metadata to PostgreSQL and records an immutable audit log.
    """
    stmt = select(Mission).where(Mission.id == mission_id)
    res = await db.execute(stmt)
    mission = res.scalar_one_or_none()

    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    role, can_access = await evaluate_mission_clearance(mission, current_user, db)
    if role not in (MissionRole.OWNER, MissionRole.EDITOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Role '{role}' cannot upload documents. Owner or Editor clearance required."
        )

    # Calculate cumulative mission storage
    storage_sum_stmt = select(func.coalesce(func.sum(MissionDocument.file_size_bytes), 0)).where(
        MissionDocument.mission_id == mission_id
    )
    current_used_bytes = (await db.execute(storage_sum_stmt)).scalar() or 0

    # Stream, hash, and validate
    safe_filename, mime_type, file_size, sha256_hex = await process_and_validate_upload(
        upload_file=file,
        current_mission_storage_bytes=current_used_bytes,
        user_subscription=current_user.subscription
    )

    # Persist to storage engine
    storage = get_storage_engine()
    storage_key = f"missions/{mission.id}/{uuid4().hex[:12]}_{safe_filename}"
    saved_uri = await storage.save_stream(file.file, storage_key)

    new_doc = MissionDocument(
        mission_id=mission.id,
        uploader_id=current_user.id,
        original_filename=safe_filename,
        file_type=mime_type,
        file_size_bytes=file_size,
        storage_path=saved_uri,
        sha256_hash=sha256_hex,
        is_confidential=True
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    await log_audit_event(
        db=db,
        action=AuditAction.DOCUMENT_UPLOADED,
        entity="DOCUMENT",
        user_id=current_user.id,
        entity_id=new_doc.id,
        metadata_json={
            "filename": safe_filename,
            "sha256": sha256_hex,
            "size_bytes": file_size,
            "mission_id": str(mission_id)
        },
        request=request
    )

    return new_doc


@router.get("/missions/{mission_id}/documents", response_model=list[MissionDocumentResponse])
async def list_mission_documents(
    mission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists documents attached to a Mission.
    Enforces authorization: Only creators, invited collaborators, and verified purchasers
    can inspect document records.
    """
    stmt = select(Mission).where(Mission.id == mission_id)
    mission = (await db.execute(stmt)).scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    role, can_view = await evaluate_mission_clearance(mission, current_user, db)
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document vault is locked. Complete license purchase or request collaboration to inspect."
        )

    docs_stmt = select(MissionDocument).where(MissionDocument.mission_id == mission_id).order_by(MissionDocument.created_at.desc())
    return (await db.execute(docs_stmt)).scalars().all()


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Permanently purges document from storage and database."""
    stmt = select(MissionDocument).where(MissionDocument.id == document_id)
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Check permission on parent mission
    mission_stmt = select(Mission).where(Mission.id == doc.mission_id)
    mission = (await db.execute(mission_stmt)).scalar_one()

    role, _ = await evaluate_mission_clearance(mission, current_user, db)
    if role not in (MissionRole.OWNER, MissionRole.EDITOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner or editor can delete documents.")

    storage = get_storage_engine()
    await storage.delete_object(doc.storage_path)

    await db.delete(doc)
    await db.commit()

    await log_audit_event(
        db=db,
        action=AuditAction.DOCUMENT_DELETED,
        entity="DOCUMENT",
        user_id=current_user.id,
        entity_id=document_id,
        metadata_json={"original_filename": doc.original_filename, "sha256": doc.sha256_hash},
        request=request
    )

    return {"message": f"Document '{doc.original_filename}' successfully purged from vault."}
