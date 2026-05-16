from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..database import get_db
from ..models.user import User, LoginHistory
from ..schemas.auth import (
    LoginRequest, TokenResponse, ChangePasswordRequest, RefreshRequest
)
from ..core.security import (
    verify_password, hash_password, create_access_token, create_refresh_token,
    decode_token, get_current_user, password_meets_policy
)
from ..core.permissions import ROLE_PERMISSIONS

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:500]

    user = db.scalar(select(User).where(User.username == payload.username))
    history = LoginHistory(user_id=user.id if user else None, username_attempted=payload.username,
                           ip_address=ip, user_agent=ua, success=False)
    if not user:
        history.failure_reason = "User not found"
        db.add(history); db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.locked_until and user.locked_until > datetime.utcnow():
        history.failure_reason = "Account locked"
        db.add(history); db.commit()
        raise HTTPException(status_code=423,
                            detail=f"Account locked until {user.locked_until.isoformat()}")

    if not user.is_active:
        history.failure_reason = "User inactive"
        db.add(history); db.commit()
        raise HTTPException(status_code=401, detail="User inactive")

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        history.failure_reason = "Wrong password"
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGINS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOCKOUT_MINUTES)
            history.failure_reason = "Wrong password — account locked"
        db.add(history); db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Success
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    history.success = True
    history.failure_reason = None
    db.add(history); db.commit()

    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id, user.role)
    return TokenResponse(
        access_token=access, refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        force_password_change=user.force_password_change,
        user={"id": user.id, "username": user.username, "email": user.email,
              "full_name": user.full_name, "role": user.role,
              "permissions": [p.value for p in ROLE_PERMISSIONS.get(user.role, [])]},
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    user = db.scalar(select(User).where(User.id == int(data["sub"])))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id, user.role)
    return TokenResponse(access_token=access, refresh_token=new_refresh,
                         expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                         force_password_change=user.force_password_change,
                         user={"id": user.id, "username": user.username, "role": user.role,
                               "permissions": [p.value for p in ROLE_PERMISSIONS.get(user.role, [])]})


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"ok": True, "message": "Logged out (client should discard tokens)"}


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    ok, msg = password_meets_policy(payload.new_password)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    current_user.password_hash = hash_password(payload.new_password)
    current_user.force_password_change = False
    db.commit()
    return {"ok": True, "message": "Password changed"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, "username": current_user.username,
        "email": current_user.email, "full_name": current_user.full_name,
        "role": current_user.role,
        "force_password_change": current_user.force_password_change,
        "permissions": [p.value for p in ROLE_PERMISSIONS.get(current_user.role, [])],
    }
