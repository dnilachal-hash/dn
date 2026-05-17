"""User management router (super_admin only)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, Permission
from app.core.security import hash_password, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_USERS)),
):
    users = list(db.execute(select(User).order_by(User.username)).scalars())
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_USERS)),
):
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{payload.username}' already exists")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
        force_password_change=payload.force_password_change,
    )
    db.add(user)
    db.flush()
    log_action(db, current_user, "CREATE_USER", "user", user.id,
               None, {"username": payload.username, "role": payload.role}, request=request)
    db.commit()
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_USERS)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_USERS)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old = {"role": str(user.role), "is_active": user.is_active}
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)

    log_action(db, current_user, "UPDATE_USER", "user", user_id, old,
               payload.model_dump(exclude_none=True), request=request)
    db.commit()
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_USERS)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user.is_active = False
    log_action(db, current_user, "DISABLE_USER", "user", user_id, request=request)
    db.commit()


@router.post("/{user_id}/reset-password", response_model=UserOut)
def reset_password(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_USERS)),
):
    """Reset a user's password to a temporary one and force change on next login."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    temp_password = f"Temp@{user_id}Reset"
    user.password_hash = hash_password(temp_password)
    user.force_password_change = True
    log_action(db, current_user, "RESET_PASSWORD", "user", user_id, request=request)
    db.commit()
    return UserOut.model_validate(user)


@router.post("/{user_id}/unlock", response_model=UserOut)
def unlock_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_USERS)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.locked_until = None
    user.failed_login_attempts = 0
    log_action(db, current_user, "UNLOCK_USER", "user", user_id, request=request)
    db.commit()
    return UserOut.model_validate(user)
