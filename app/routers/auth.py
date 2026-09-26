from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    generate_continuum_id,
    create_access_token,
    create_refresh_token,
    decode_token
)
from backend.app.core.permissions import get_current_user
from backend.app.core.audit import log_audit_event, AuditAction
from backend.app.models.user import User, UserSettings
from backend.app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Registers a new user and issues a unique permanent Continuum ID (e.g. CNT-7F42-91K8)."""
    # Check existing email
    stmt = select(User).where(User.email == req.email.lower().strip())
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists."
        )

    # Generate distinct Continuum ID
    cnt_id = generate_continuum_id()
    # Check uniqueness
    while (await db.execute(select(User).where(User.continuum_id == cnt_id))).scalar_one_or_none():
        cnt_id = generate_continuum_id()

    hashed_pw = get_password_hash(req.password)
    
    new_user = User(
        continuum_id=cnt_id,
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        email=req.email.lower().strip(),
        phone=req.phone,
        country=req.country,
        province_region=req.province_region,
        subscription="FREE",
        password_hash=hashed_pw,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    await db.flush()

    # User settings default: Dark mode strictly false by default
    new_settings = UserSettings(
        user_id=new_user.id,
        dark_mode=False,
        email_notifications=True,
        release_reminder_days=30,
        popia_consent_at=datetime.now(timezone.utc) if req.popia_consent else None
    )
    db.add(new_settings)
    await db.commit()
    await db.refresh(new_user)

    await log_audit_event(
        db=db,
        action="USER_REGISTERED",
        entity="USER",
        user_id=new_user.id,
        entity_id=new_user.id,
        metadata_json={"continuum_id": cnt_id, "country": req.country},
        request=request
    )

    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticates user with email and password, returning JWT access & refresh tokens."""
    stmt = select(User).where(User.email == req.email.lower().strip())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated under POPIA."
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    await log_audit_event(
        db=db,
        action="USER_LOGIN",
        entity="USER",
        user_id=user.id,
        entity_id=user.id,
        metadata_json={"continuum_id": user.continuum_id},
        request=request
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Exchanges a valid refresh token for a fresh access token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    user_id = payload.get("sub")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=3600)

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Retrieves authenticated user's private profile and settings."""
    stmt = select(UserSettings).where(UserSettings.user_id == current_user.id)
    res = await db.execute(stmt)
    current_user.settings = res.scalar_one_or_none()
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Invalidates client session. Handled on client by token destruction and server audit."""
    return {"message": "Successfully signed out of Continuum session."}
