"""RBAC permission catalog and role-permission matrix."""
from enum import Enum
from fastapi import Depends, HTTPException, status
from .security import get_current_user


class Permission(str, Enum):
    EMPLOYEE_VIEW = "employee.view"
    EMPLOYEE_CREATE = "employee.create"
    EMPLOYEE_EDIT = "employee.edit"
    EMPLOYEE_DELETE = "employee.delete"
    EMPLOYEE_VIEW_SENSITIVE = "employee.view_sensitive"

    SALARY_VIEW = "salary.view"
    SALARY_CREATE = "salary.create"
    SALARY_REVISE = "salary.revise"

    PAYROLL_VIEW = "payroll.view"
    PAYROLL_GENERATE = "payroll.generate"
    PAYROLL_APPROVE = "payroll.approve"
    PAYROLL_REJECT = "payroll.reject"
    PAYROLL_LOCK = "payroll.lock"
    PAYROLL_UNLOCK = "payroll.unlock"
    PAYROLL_PAID = "payroll.mark_paid"
    PAYROLL_FNF = "payroll.fnf"

    REPORT_VIEW = "report.view"
    REPORT_EXPORT = "report.export"

    STATUTORY_VIEW = "statutory.view"
    STATUTORY_EDIT = "statutory.edit"
    TDS_OVERRIDE = "tds.override"

    AUDIT_VIEW = "audit.view"
    AUDIT_EXPORT = "audit.export"

    USER_MANAGE = "user.manage"
    IMPORT_BULK = "import.bulk"
    BACKUP_TAKE = "backup.take"
    BACKUP_RESTORE = "backup.restore"

    DASHBOARD_VIEW = "dashboard.view"


ALL_PERMISSIONS = [p for p in Permission]

ROLE_PERMISSIONS: dict[str, list[Permission]] = {
    "super_admin": ALL_PERMISSIONS,
    "admin": [p for p in ALL_PERMISSIONS if p not in {Permission.USER_MANAGE}],
    "hr_manager": [
        Permission.DASHBOARD_VIEW,
        Permission.EMPLOYEE_VIEW, Permission.EMPLOYEE_CREATE, Permission.EMPLOYEE_EDIT,
        Permission.EMPLOYEE_VIEW_SENSITIVE,
        Permission.SALARY_VIEW, Permission.SALARY_CREATE, Permission.SALARY_REVISE,
        Permission.PAYROLL_VIEW, Permission.PAYROLL_GENERATE,
        Permission.REPORT_VIEW, Permission.REPORT_EXPORT,
        Permission.STATUTORY_VIEW,
        Permission.IMPORT_BULK,
    ],
    "payroll_executive": [
        Permission.DASHBOARD_VIEW,
        Permission.EMPLOYEE_VIEW,
        Permission.SALARY_VIEW,
        Permission.PAYROLL_VIEW, Permission.PAYROLL_GENERATE,
        Permission.REPORT_VIEW, Permission.REPORT_EXPORT,
        Permission.STATUTORY_VIEW,
    ],
    "accounts_user": [
        Permission.DASHBOARD_VIEW,
        Permission.EMPLOYEE_VIEW,
        Permission.PAYROLL_VIEW, Permission.PAYROLL_PAID,
        Permission.REPORT_VIEW, Permission.REPORT_EXPORT,
    ],
    "auditor": [
        Permission.DASHBOARD_VIEW,
        Permission.EMPLOYEE_VIEW,
        Permission.SALARY_VIEW,
        Permission.PAYROLL_VIEW,
        Permission.REPORT_VIEW, Permission.REPORT_EXPORT,
        Permission.AUDIT_VIEW, Permission.AUDIT_EXPORT,
        Permission.STATUTORY_VIEW,
    ],
}


def has_permission(role: str, perm: Permission) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, [])


def require_permission(perm: Permission):
    def _check(current_user = Depends(get_current_user)):
        if not has_permission(current_user.role, perm):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Missing permission: {perm.value}")
        return current_user
    return _check


def require_role(*roles: str):
    def _check(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Requires one of roles: {roles}")
        return current_user
    return _check
