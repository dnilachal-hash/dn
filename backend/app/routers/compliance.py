from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from ..database import get_db
from ..models.compliance import ComplianceAlert
from ..models.user import User, AuditLog
from ..core.permissions import require_permission, Permission, require_role
from ..services.audit_service import log_action

router = APIRouter(tags=["compliance"])


@router.get("/compliance/alerts")
def list_alerts(severity: str | None = None, resolved: bool = False,
                db: Session = Depends(get_db),
                current_user: User = Depends(require_permission(Permission.PAYROLL_VIEW))):
    q = select(ComplianceAlert).where(ComplianceAlert.is_resolved == resolved)
    if severity:
        q = q.where(ComplianceAlert.severity == severity)
    rows = db.scalars(q.order_by(ComplianceAlert.created_at.desc()).limit(500)).all()
    return [{"id": a.id, "employee_id": a.employee_id,
             "payroll_month_id": a.payroll_month_id,
             "type": a.alert_type, "severity": a.severity,
             "message": a.message, "is_resolved": a.is_resolved,
             "created_at": a.created_at} for a in rows]


@router.post("/compliance/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(require_permission(Permission.PAYROLL_GENERATE))):
    a = db.get(ComplianceAlert, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    a.is_resolved = True
    a.resolved_by = current_user.id
    a.resolved_at = datetime.utcnow()
    log_action(db, current_user, "COMPLIANCE_RESOLVE", "ComplianceAlert", a.id)
    db.commit()
    return {"ok": True}


@router.get("/audit/logs")
def audit_logs(entity_type: str | None = None, user_id: int | None = None,
               limit: int = 200, db: Session = Depends(get_db),
               current_user: User = Depends(require_permission(Permission.AUDIT_VIEW))):
    q = select(AuditLog)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    rows = db.scalars(q.order_by(AuditLog.timestamp.desc()).limit(limit)).all()
    return [{"id": r.id, "user": r.username, "action": r.action,
             "entity": r.entity_type, "entity_id": r.entity_id,
             "old": r.old_values, "new": r.new_values,
             "ip": r.ip_address, "ts": r.timestamp} for r in rows]
