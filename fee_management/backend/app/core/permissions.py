"""Role-based permission system."""
import enum
from functools import lru_cache
from typing import Set

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user


class Permission(str, enum.Enum):
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    MANAGE_STUDENTS = "manage_students"
    VIEW_STUDENTS = "view_students"
    MANAGE_COURSES = "manage_courses"
    VIEW_COURSES = "view_courses"
    MANAGE_FEE_HEADS = "manage_fee_heads"
    VIEW_FEE_HEADS = "view_fee_heads"
    MANAGE_FEE_STRUCTURES = "manage_fee_structures"
    VIEW_FEE_STRUCTURES = "view_fee_structures"
    COLLECT_FEES = "collect_fees"
    VIEW_RECEIPTS = "view_receipts"
    EDIT_RECEIPTS = "edit_receipts"
    CANCEL_RECEIPTS = "cancel_receipts"
    BULK_UPLOAD = "bulk_upload"
    ROLLBACK_UPLOAD = "rollback_upload"
    VIEW_REPORTS = "view_reports"
    EXPORT_REPORTS = "export_reports"
    MANAGE_FINANCIAL_YEARS = "manage_financial_years"
    MANAGE_SETTINGS = "manage_settings"
    BACKUP_RESTORE = "backup_restore"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_PAYMENT_MODES = "manage_payment_modes"


_ALL = set(Permission)

ROLE_PERMISSIONS: dict[str, Set[Permission]] = {
    "super_admin": _ALL,
    "accounts_user": {
        Permission.MANAGE_STUDENTS,
        Permission.VIEW_STUDENTS,
        Permission.COLLECT_FEES,
        Permission.VIEW_RECEIPTS,
        Permission.VIEW_REPORTS,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_FEE_STRUCTURES,
        Permission.VIEW_FEE_HEADS,
        Permission.VIEW_COURSES,
        Permission.BULK_UPLOAD,
    },
    "viewer": {
        Permission.VIEW_STUDENTS,
        Permission.VIEW_RECEIPTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_FEE_STRUCTURES,
        Permission.VIEW_FEE_HEADS,
        Permission.VIEW_COURSES,
    },
    "auditor": {
        Permission.VIEW_STUDENTS,
        Permission.VIEW_RECEIPTS,
        Permission.VIEW_REPORTS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.VIEW_FEE_STRUCTURES,
        Permission.VIEW_FEE_HEADS,
        Permission.VIEW_COURSES,
    },
}


def has_permission(user, perm: Permission) -> bool:
    role = user.role if isinstance(user.role, str) else user.role.value
    perms = ROLE_PERMISSIONS.get(role, set())
    return perm in perms


def require_permission(perm: Permission):
    """FastAPI dependency factory that checks a permission."""
    def _dep(current_user=Depends(get_current_user)):
        if not has_permission(current_user, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{perm.value}' required.",
            )
        return current_user
    return _dep


def require_role(*roles: str):
    """FastAPI dependency factory that restricts to specific roles."""
    def _dep(current_user=Depends(get_current_user)):
        role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role must be one of: {', '.join(roles)}",
            )
        return current_user
    return _dep
