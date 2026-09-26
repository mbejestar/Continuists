from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class UserRegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    country: str = "South Africa"
    province_region: Optional[str] = "Gauteng"
    popia_consent: bool = Field(True, description="Consent under POPIA for processing personal knowledge archives")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserSettingsResponse(BaseModel):
    dark_mode: bool
    email_notifications: bool
    release_reminder_days: int
    popia_consent_at: Optional[datetime] = None
    biometric_recovery_enabled: bool

class UserSettingsUpdate(BaseModel):
    dark_mode: Optional[bool] = None
    email_notifications: Optional[bool] = None
    release_reminder_days: Optional[int] = None
    biometric_recovery_enabled: Optional[bool] = None

class UserResponse(BaseModel):
    id: UUID
    continuum_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    country: str
    province_region: Optional[str] = None
    profile_photo_url: Optional[str] = None
    subscription: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    settings: Optional[UserSettingsResponse] = None

    class Config:
        from_attributes = True

class PublicUserProfile(BaseModel):
    continuum_id: str
    first_name: str
    last_name: str
    country: str
    province_region: Optional[str] = None
    subscription: str

    class Config:
        from_attributes = True
