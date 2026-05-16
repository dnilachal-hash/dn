from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ..database import get_db
from ..models.employee import Employee, Department
from ..models.payroll import PayrollMonth, PayrollRecord, PayrollStatus
from ..models.compliance import ComplianceAlert
from ..models.user import User
from ..core.permissions import require_permission, Permission

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(db: Session = Depends(get_db),
          current_user: User = Depends(require_permission(Permission.DASHBOARD_VIEW))):
    active = db.scalar(select(func.count(Employee.id)).where(Employee.is_active == True)) or 0
    teaching = db.scalar(select(func.count(Employee.id))
        .join(Department).where(Department.type == "TEACHING", Employee.is_active == True)) or 0
    non_teaching = active - teaching
    pending_approval = db.scalar(select(func.count(PayrollMonth.id))
        .where(PayrollMonth.status == PayrollStatus.GENERATED.value)) or 0
    critical_alerts = db.scalar(select(func.count(ComplianceAlert.id))
        .where(ComplianceAlert.severity == "CRITICAL",
               ComplianceAlert.is_resolved == False)) or 0
    warnings = db.scalar(select(func.count(ComplianceAlert.id))
        .where(ComplianceAlert.severity == "WARNING",
               ComplianceAlert.is_resolved == False)) or 0
    latest_pm = db.scalar(select(PayrollMonth)
        .order_by(PayrollMonth.year.desc(), PayrollMonth.month.desc()))
    latest_gross = 0
    if latest_pm:
        latest_gross = float(db.scalar(
            select(func.coalesce(func.sum(PayrollRecord.gross_salary), 0))
            .where(PayrollRecord.payroll_month_id == latest_pm.id)) or 0)
    return {
        "active_employees": active,
        "teaching_employees": teaching,
        "non_teaching_employees": non_teaching,
        "pending_approvals": pending_approval,
        "critical_alerts": critical_alerts,
        "warnings": warnings,
        "latest_month": f"{latest_pm.month}/{latest_pm.year}" if latest_pm else None,
        "latest_month_status": latest_pm.status if latest_pm else None,
        "latest_month_gross": latest_gross,
    }


@router.get("/department-headcount")
def department_headcount(db: Session = Depends(get_db),
                          current_user: User = Depends(require_permission(Permission.DASHBOARD_VIEW))):
    rows = db.execute(
        select(Department.name, Department.type, func.count(Employee.id))
        .join(Employee, Employee.department_id == Department.id, isouter=True)
        .where(Employee.is_active == True)
        .group_by(Department.id)
    ).all()
    return [{"department": r[0], "type": r[1], "count": r[2]} for r in rows]


@router.get("/payroll-trend")
def payroll_trend(months: int = 12, db: Session = Depends(get_db),
                   current_user: User = Depends(require_permission(Permission.DASHBOARD_VIEW))):
    rows = db.execute(
        select(PayrollMonth.month, PayrollMonth.year,
               func.coalesce(func.sum(PayrollRecord.gross_salary), 0).label("gross"),
               func.coalesce(func.sum(PayrollRecord.net_salary), 0).label("net"),
               func.coalesce(func.sum(PayrollRecord.ctc), 0).label("ctc"))
        .join(PayrollRecord, PayrollRecord.payroll_month_id == PayrollMonth.id, isouter=True)
        .group_by(PayrollMonth.id)
        .order_by(PayrollMonth.year.desc(), PayrollMonth.month.desc())
        .limit(months)
    ).all()
    return [{"period": f"{r.month:02d}/{r.year}",
             "gross": float(r.gross), "net": float(r.net), "ctc": float(r.ctc)}
            for r in reversed(rows)]
