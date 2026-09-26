import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates bcrypt hash for password."""
    return pwd_context.hash(password)

def generate_continuum_id() -> str:
    """
    Generates a unique permanent Continuum ID.
    Example: CNT-7F42-91K8
    The ID is NOT derived from email or personal data (POPIA compliant).
    """
    chars = string.ascii_uppercase + string.digits
    # Remove easily confused characters: 0, O, 1, I
    clean_chars = "".join([c for c in chars if c not in "0O1I"])
    part1 = "".join(secrets.choice(clean_chars) for _ in range(4))
    part2 = "".join(secrets.choice(clean_chars) for _ in range(4))
    return f"CNT-{part1}-{part2}"

def generate_mission_continuum_id() -> str:
    """
    Generates a unique public mission ID.
    Example: MSN-4B82-9Q1Z
    """
    chars = string.ascii_uppercase + string.digits
    clean_chars = "".join([c for c in chars if c not in "0O1I"])
    part1 = "".join(secrets.choice(clean_chars) for _ in range(4))
    part2 = "".join(secrets.choice(clean_chars) for _ in range(4))
    return f"MSN-{part1}-{part2}"

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: Union[str, Any]) -> str:
    """Creates a signed JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
