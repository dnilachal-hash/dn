from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models.user import User, LoginHistory
from ..schemas.user import UserCreate, UserUpdate, UserOut
from ..schemas.auth import ResetPasswordRequest
from ..core.security import hash_password, password_meets_policy
from ..core.permissions import require_role, require_permission, Permission, ROLE_PERMISSIONS
from ..services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db),
               current_user: User = Depends(require_role("super_admin", "admin"))):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db),
                current_user: User = Depends(require_role("super_admin"))):
    if payload.role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of {list(ROLE_PERMISSIONS)}")
    ok, msg = password_meets_policy(payload.password)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="Username taken")
    u = User(username=payload.username, email=payload.email, full_name=payload.full_name,
             password_hash=hash_password(payload.password), role=payload.role,
             force_password_change=True, created_by=current_user.id)
    db.add(u); db.flush()
    log_action(db, current_user, "USER_CREATE", "User", u.id, None, {"username": u.username, "role": u.role})
    db.commit(); db.refresh(u)
    return u


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(require_role("super_admin"))):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    old = {"role": u.role, "is_active": u.is_active}
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    log_action(db, current_user, "USER_UPDATE", "User", u.id, old,
               {"role": u.role, "is_active": u.is_active})
    db.commit(); db.refresh(u)
    return u


@router.post("/{user_id}/reset-password")
def reset_password(user_id: int, payload: ResetPasswordRequest,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(require_role("super_admin"))):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    ok, msg = password_meets_policy(payload.new_password)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    u.password_hash = hash_password(payload.new_password)
    u.force_password_change = True
    u.failed_login_attempts = 0
    u.locked_until = None
    log_action(db, current_user, "USER_PASSWORD_RESET", "User", u.id)
    db.commit()
    return {"ok": True}


@router.get("/{user_id}/login-history")
def login_history(user_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("super_admin", "admin"))):
    rows = db.scalars(select(LoginHistory).where(LoginHistory.user_id == user_id)
                      .order_by(LoginHistory.login_at.desc()).limit(200)).all()
    return [{"login_at": r.login_at, "ip": r.ip_address, "ua": r.user_agent,
             "success": r.success, "reason": r.failure_reason} for r in rows]
