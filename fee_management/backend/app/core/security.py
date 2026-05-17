"""Security utilities: hashing, encryption, JWT, dependencies."""
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")
ALGORITHM = "HS256"


# ──────────────────────────────────────────
# Password hashing
# ──────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode()[:72], bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode()[:72], hashed.encode())
    except Exception:
        return False


def password_meets_policy(pw: str) -> bool:
    """Min 8 chars, at least one uppercase, one digit, one special character."""
    if len(pw) < 8:
        return False
    if not any(c.isupper() for c in pw):
        return False
    if not any(c.isdigit() for c in pw):
        return False
    special = set(r'!@#$%^&*()_+-=[]{}|;\':",.<>?/`~\\')
    if not any(c in special for c in pw):
        return False
    return True


# ──────────────────────────────────────────
# Fernet encryption
# ──────────────────────────────────────────

def _fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode()
    try:
        return Fernet(key)
    except Exception:
        # Fall back: pad/truncate to 32 bytes and base64url-encode
        padded = base64.urlsafe_b64encode((settings.ENCRYPTION_KEY * 4).encode()[:32])
        return Fernet(padded)


def encrypt(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value
    try:
        return _fernet().decrypt(value.encode()).decode()
    except Exception:
        return None


# ──────────────────────────────────────────
# JWT tokens
# ──────────────────────────────────────────

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["type"] = "access"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ──────────────────────────────────────────
# FastAPI dependency: current user
# ──────────────────────────────────────────

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from app.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exception

    # Check lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.isoformat()}",
        )

    return user
