"""Authentication router."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, password_meets_policy,
)
from app.database import get_db
from app.models.user import User, LoginHistory
from app.schemas.user import LoginRequest, TokenResponse, UserOut, ChangePasswordRequest, RefreshRequest
from app.services.audit_service import log_action
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    ip = _get_ip(request)
    ua = request.headers.get("user-agent", "")

    def _log_attempt(success: bool, user_obj=None):
        hist = LoginHistory(
            user_id=user_obj.id if user_obj else None,
            login_at=datetime.utcnow(),
            ip_address=ip,
            user_agent=ua,
            success=success,
        )
        db.add(hist)
        db.commit()

    if not user:
        _log_attempt(False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        _log_attempt(False, user)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    # Check lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        _log_attempt(False, user)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked until {user.locked_until.strftime('%Y-%m-%d %H:%M')} UTC",
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGINS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
        _log_attempt(False, user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Success
    user.failed_login_attempts = 0
    user.locked_until = None

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access = create_access_token({"sub": str(user.id), "role": role_str})
    refresh = create_refresh_token({"sub": str(user.id), "role": role_str})

    _log_attempt(True, user)
    log_action(db, user, "LOGIN", "user", user.id, request=request)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user = db.get(User, int(data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access = create_access_token({"sub": str(user.id), "role": role_str})
    new_refresh = create_refresh_token({"sub": str(user.id), "role": role_str})
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        user=UserOut.model_validate(user),
    )


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Update last login_history logout_at
    hist = db.scalar(
        select(LoginHistory)
        .where(LoginHistory.user_id == current_user.id, LoginHistory.logout_at.is_(None))
        .order_by(LoginHistory.login_at.desc())
    )
    if hist:
        hist.logout_at = datetime.utcnow()
    log_action(db, current_user, "LOGOUT", "user", current_user.id, request=request)
    db.commit()
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if not password_meets_policy(payload.new_password):
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 8 characters with uppercase, digit, and special character.",
        )

    current_user.password_hash = hash_password(payload.new_password)
    current_user.force_password_change = False
    log_action(db, current_user, "CHANGE_PASSWORD", "user", current_user.id, request=request)
    db.commit()
    return {"message": "Password changed successfully"}
