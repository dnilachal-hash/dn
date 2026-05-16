from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from cryptography.fernet import Fernet
import base64

from ..config import settings
from ..database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def _fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.encode()
    # Accept either raw base64 fernet key (44 chars) or arbitrary string padded
    try:
        return Fernet(key)
    except Exception:
        padded = base64.urlsafe_b64encode((settings.ENCRYPTION_KEY * 4).encode()[:32])
        return Fernet(padded)


def encrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except Exception:
        return None


def mask_pan(pan: str | None) -> str | None:
    if not pan or len(pan) < 4:
        return pan
    return "XXXXX" + pan[-4:]


def mask_aadhaar(aadhaar: str | None) -> str | None:
    if not aadhaar or len(aadhaar) < 4:
        return aadhaar
    return "XXXX-XXXX-" + aadhaar[-4:]


def mask_account(acc: str | None) -> str | None:
    if not acc or len(acc) < 4:
        return acc
    return "X" * (len(acc) - 4) + acc[-4:]


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8")[:72], salt).decode("utf-8")


def create_token(subject: str | int, role: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(subject), "role": role, "exp": expire, "type": token_type}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | int, role: str) -> str:
    return create_token(subject, role, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(subject: str | int, role: str) -> str:
    return create_token(subject, role, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from ..models.user import User
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = int(payload["sub"])
    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def password_meets_policy(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if not any(c in "!@#$%^&*()_+-=[]{};:,.<>?/" for c in password):
        return False, "Password must contain at least one special character"
    return True, "OK"
