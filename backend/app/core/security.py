"""JWT authentication utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import structlog
from jose import JWTError, jwt  # type: ignore

from app.core.config import settings

logger = structlog.get_logger()


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    password_bytes = password.encode('utf-8')
    # If the password is longer than 72 bytes, bcrypt will raise a ValueError.
    # We truncate to 72 bytes to be safe.
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    try:
        plain_bytes = plain_password.encode('utf-8')
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
        return bcrypt.checkpw(plain_bytes, hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("Token decode failed", error=str(e))
        return None


def create_password_reset_token(email: str) -> str:
    """Create a short-lived password reset token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    data: dict[str, Any] = {"sub": email, "type": "password_reset", "exp": expire}
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
