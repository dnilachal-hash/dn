from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from io import BytesIO

from ..database import get_db
from ..models.payroll import PayrollMonth, PayrollRecord, PayrollStatus, PaymentStatus
from ..models.employee import Employee
from ..models.user import User
from ..schemas.payroll import (
    PayrollMonthCreate, PayrollMonthOut, PayrollRecordOut,
    PayrollGenerateRequest, UnlockRequest, MarkPaidRequest
)
from ..core.permissions import require_permission, Permission
from ..core.exceptions import PayrollLockedError
from ..services.payroll_service import generate_payroll_month
from ..services.audit_service import log_action
from ..services.pdf_service import generate_payslip_pdf
from ..services.excel_service import generate_payslip_excel
from ..services.report_service import get_org

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.get("/months", response_model=list[PayrollMonthOut])
def list_months(db: Session = Depends(get_db),
                current_user: User = Depends(require_permission(Permission.PAYROLL_VIEW))):
    return db.scalars(select(PayrollMonth).order_by(PayrollMonth.year.desc(),
                                                    PayrollMonth.month.desc())).all()


@router.post("/months", response_model=PayrollMonthOut, status_code=201)
def create_month(payload: PayrollMonthCreate, db: Session = Depends(get_db),
                 current_user: User = Depends(require_permission(Permission.PAYROLL_GENERATE))):
    existing = db.scalar(select(PayrollMonth).where(
        PayrollMonth.financial_year_id == payload.financial_year_id,
        PayrollMonth.month == payload.month,
        PayrollMonth.year == payload.year))
    if existing:
        return existing
    pm = PayrollMonth(**payload.model_dump(), status=PayrollStatus.DRAFT.value)
    db.add(pm); db.flush()
    log_action(db, current_user, "PAYROLL_MONTH_CREATE", "PayrollMonth", pm.id,
               None, payload.model_dump())
    db.commit(); db.refresh(pm)
    return pm


@router.post("/months/{month_id}/generate")
def generate(month_id: int, payload: PayrollGenerateRequest | None = None,
             db: Session = Depends(get_db),
             current_user: User = Depends(require_permission(Permission.PAYROLL_GENERATE))):
    pm = db.get(PayrollMonth, month_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Payroll month not found")
    payload = payload or PayrollGenerateRequest()
    result = generate_payroll_month(db, pm, current_user.id,
                                     payload.employee_ids, payload.department_id)
    log_action(db, current_user, "PAYROLL_GENERATE", "PayrollMonth", pm.id, None, result)
    db.commit()
    return result


@router.get("/months/{month_id}/records", response_model=list[PayrollRecordOut])
def list_records(month_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(require_permission(Permission.PAYROLL_VIEW))):
    return db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == month_id).order_by(PayrollRecord.id)).all()


@router.post("/months/{month_id}/approve")
def approve(month_id: int, db: Session = Depends(get_db),
            current_user: User = Depends(require_permission(Permission.PAYROLL_APPROVE))):
    pm = db.get(PayrollMonth, month_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Not found")
    if pm.status not in (PayrollStatus.GENERATED.value, PayrollStatus.DRAFT.value):
        raise HTTPException(status_code=409, detail=f"Cannot approve from status {pm.status}")
    pm.status = PayrollStatus.APPROVED.value
    pm.approved_at = datetime.utcnow()
    pm.approved_by = current_user.id
    db.execute(
        PayrollRecord.__table__.update()
        .where(PayrollRecord.payroll_month_id == month_id)
        .values(status=PayrollStatus.APPROVED.value)
    )
    log_action(db, current_user, "PAYROLL_APPROVE", "PayrollMonth", pm.id)
    db.commit()
    return {"ok": True}


@router.post("/months/{month_id}/lock")
def lock(month_id: int, db: Session = Depends(get_db),
         current_user: User = Depends(require_permission(Permission.PAYROLL_LOCK))):
    pm = db.get(PayrollMonth, month_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Not found")
    if pm.status != PayrollStatus.APPROVED.value:
        raise HTTPException(status_code=409, detail="Only APPROVED months can be locked")
    pm.status = PayrollStatus.LOCKED.value
    pm.locked_at = datetime.utcnow()
    pm.locked_by = current_user.id
    db.execute(
        PayrollRecord.__table__.update()
        .where(PayrollRecord.payroll_month_id == month_id)
        .values(status=PayrollStatus.LOCKED.value)
    )
    log_action(db, current_user, "PAYROLL_LOCK", "PayrollMonth", pm.id)
    db.commit()
    return {"ok": True}


@router.post("/months/{month_id}/unlock")
def unlock(month_id: int, payload: UnlockRequest, db: Session = Depends(get_db),
           current_user: User = Depends(require_permission(Permission.PAYROLL_UNLOCK))):
    pm = db.get(PayrollMonth, month_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Not found")
    if pm.status != PayrollStatus.LOCKED.value:
        raise HTTPException(status_code=409, detail="Not locked")
    pm.status = PayrollStatus.APPROVED.value
    pm.unlock_reason = payload.reason
    pm.locked_at = None
    log_action(db, current_user, "PAYROLL_UNLOCK", "PayrollMonth", pm.id, None,
               {"reason": payload.reason})
    db.commit()
    return {"ok": True}


@router.post("/months/{month_id}/mark-paid")
def mark_paid(month_id: int, payload: MarkPaidRequest, db: Session = Depends(get_db),
              current_user: User = Depends(require_permission(Permission.PAYROLL_PAID))):
    pm = db.get(PayrollMonth, month_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Not found")
    pm.status = PayrollStatus.PAID.value
    db.execute(
        PayrollRecord.__table__.update()
        .where(PayrollRecord.payroll_month_id == month_id)
        .values(status=PayrollStatus.PAID.value,
                payment_status=PaymentStatus.PAID.value,
                payment_date=payload.payment_date,
                payment_reference=payload.payment_reference)
    )
    log_action(db, current_user, "PAYROLL_PAID", "PayrollMonth", pm.id,
               None, payload.model_dump(mode="json"))
    db.commit()
    return {"ok": True}


@router.get("/records/{record_id}/payslip")
def download_payslip(record_id: int, format: str = "pdf",
                     db: Session = Depends(get_db),
                     current_user: User = Depends(require_permission(Permission.PAYROLL_VIEW))):
    rec = db.get(PayrollRecord, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    emp = db.get(Employee, rec.employee_id)
    pm = db.get(PayrollMonth, rec.payroll_month_id)
    org = get_org(db)
    fname = f"payslip_{emp.emp_code}_{pm.year}_{pm.month:02d}"
    if format == "xlsx":
        data = generate_payslip_excel(emp, rec, pm, org)
        return StreamingResponse(
            BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={fname}.xlsx"})
    data = generate_payslip_pdf(org, emp, rec, pm)
    return StreamingResponse(BytesIO(data), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={fname}.pdf"})
