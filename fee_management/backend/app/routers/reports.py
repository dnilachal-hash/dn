"""Reports router."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, Permission
from app.database import get_db
from app.models.org import FinancialYear
from app.services import report_service as rs
from app.services.pdf_service import generate_report_pdf
from app.services.excel_service import generate_report_excel
from app.services.audit_service import log_action

router = APIRouter(prefix="/reports", tags=["reports"])


def _active_fy_id(db: Session) -> Optional[int]:
    fy = db.scalar(select(FinancialYear).where(FinancialYear.is_active == True))
    return fy.id if fy else None


# ──────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.dashboard_stats(db, current_user)


# ──────────────────────────────────────────
# Daily collection
# ──────────────────────────────────────────

@router.get("/daily-collection")
def daily_collection(
    report_date: Optional[date] = Query(None),
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    for_date = report_date or date.today()
    return rs.daily_collection(db, for_date, {"fy_id": fy_id})


# ──────────────────────────────────────────
# Monthly collection
# ──────────────────────────────────────────

@router.get("/monthly-collection")
def monthly_collection(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    return rs.monthly_collection(db, y, m, {"fy_id": fy_id})


# ──────────────────────────────────────────
# FY summary
# ──────────────────────────────────────────

@router.get("/fy-summary")
def fy_summary(
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    fid = fy_id or _active_fy_id(db)
    if not fid:
        raise HTTPException(status_code=404, detail="No active financial year")
    return rs.fy_summary(db, fid)


# ──────────────────────────────────────────
# Student ledger
# ──────────────────────────────────────────

@router.get("/student-ledger/{student_id}")
def student_ledger(
    student_id: int,
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.student_ledger(db, student_id, fy_id)


# ──────────────────────────────────────────
# Fee head wise
# ──────────────────────────────────────────

@router.get("/fee-head-wise")
def fee_head_wise(
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.fee_head_wise(db, {"fy_id": fy_id, "start_date": start_date, "end_date": end_date})


# ──────────────────────────────────────────
# Payment mode wise
# ──────────────────────────────────────────

@router.get("/payment-mode-wise")
def payment_mode_wise(
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.payment_mode_wise(db, {"fy_id": fy_id, "start_date": start_date, "end_date": end_date})


# ──────────────────────────────────────────
# Dues
# ──────────────────────────────────────────

@router.get("/dues")
def dues_report(
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    fid = fy_id or _active_fy_id(db)
    return rs.dues_report(db, {"fy_id": fid})


# ──────────────────────────────────────────
# Cheque status
# ──────────────────────────────────────────

@router.get("/cheque-status")
def cheque_report(
    pmt_status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.cheque_report(db, {"status": pmt_status, "start_date": start_date, "end_date": end_date})


# ──────────────────────────────────────────
# Cancelled receipts
# ──────────────────────────────────────────

@router.get("/cancelled-receipts")
def cancelled_receipts(
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.cancelled_receipts(db, {"fy_id": fy_id, "start_date": start_date, "end_date": end_date})


# ──────────────────────────────────────────
# Corrected receipts
# ──────────────────────────────────────────

@router.get("/corrected-receipts")
def corrected_receipts(
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_REPORTS)),
):
    return rs.corrected_receipts(db, {"fy_id": fy_id, "start_date": start_date, "end_date": end_date})


# ──────────────────────────────────────────
# Audit log
# ──────────────────────────────────────────

@router.get("/audit-log")
def audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_AUDIT_LOGS)),
):
    from app.models.audit import AuditLog
    from sqlalchemy import func
    from math import ceil

    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if start_date:
        from datetime import datetime
        q = q.where(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        from datetime import datetime
        q = q.where(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    offset = (page - 1) * page_size
    logs = list(db.execute(
        q.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    ).scalars())

    return {
        "items": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "username": l.username,
                "role": l.role,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "reason": l.reason,
                "ip_address": l.ip_address,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if page_size else 1,
    }


# ──────────────────────────────────────────
# Export (Excel / PDF)
# ──────────────────────────────────────────

def _build_export_data(report: str, db: Session, fy_id: Optional[int],
                       start_date: Optional[date], end_date: Optional[date]):
    filters = {"fy_id": fy_id, "start_date": start_date, "end_date": end_date}

    if report == "fee_head_wise":
        data = rs.fee_head_wise(db, filters)
        headers = ["Fee Head", "Total Amount", "Count"]
        rows = [[d["fee_head"], d["total"], d["count"]] for d in data]
        title = "Fee Head Wise Collection"

    elif report == "payment_mode_wise":
        data = rs.payment_mode_wise(db, filters)
        headers = ["Payment Mode", "Total Amount", "Count"]
        rows = [[d["mode"], d["total"], d["count"]] for d in data]
        title = "Payment Mode Wise Collection"

    elif report == "dues":
        fid = fy_id
        data = rs.dues_report(db, {"fy_id": fid})
        headers = ["Admission No", "Student Name", "Father Name", "Course", "Batch", "Year",
                   "Total Fees", "Total Paid", "Balance"]
        rows = [[d["admission_number"], d["student_name"], d.get("father_name", ""),
                 d.get("course_name", ""), d.get("batch_name", ""), d.get("professional_year", ""),
                 d["total_fees"], d["total_paid"], d["balance"]] for d in data]
        title = "Fee Dues Report"

    elif report == "cancelled_receipts":
        data = rs.cancelled_receipts(db, filters)
        headers = ["Receipt No", "Student Name", "Admission No", "Amount", "Date", "Cancel Reason", "Cancelled At"]
        rows = [[d["receipt_number"], d["student_name"], d["admission_number"],
                 d["amount"], d["receipt_date"], d["cancel_reason"], d["cancel_at"]] for d in data]
        title = "Cancelled Receipts"

    elif report == "cheque_status":
        data = rs.cheque_report(db, filters)
        headers = ["Receipt No", "Date", "Student", "Mode", "Amount", "Cheque No", "Cheque Date", "Bank", "Status"]
        rows = [[d["receipt_number"], d["receipt_date"], d["student_name"], d["mode"],
                 d["amount"], d["cheque_number"], d["cheque_date"], d["bank_name"], d["status"]] for d in data]
        title = "Cheque Status Report"

    else:
        # Default: daily collection today
        from datetime import date as dt
        data = rs.daily_collection(db, dt.today(), filters)
        headers = ["Fee Head", "Total Amount"]
        rows = [[d["fee_head"], d["amount"]] for d in data.get("by_fee_head", [])]
        title = f"Daily Collection — {dt.today().strftime('%d %b %Y')}"

    filter_desc = " | ".join(filter(None, [
        f"FY ID: {fy_id}" if fy_id else None,
        f"From: {start_date}" if start_date else None,
        f"To: {end_date}" if end_date else None,
    ]))
    return title, headers, rows, filter_desc


@router.get("/export/excel")
def export_excel(
    report: str = Query("fee_head_wise"),
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.EXPORT_REPORTS)),
):
    title, headers, rows, filter_desc = _build_export_data(report, db, fy_id, start_date, end_date)
    excel_bytes = generate_report_excel(title, headers, rows, filter_desc)
    filename = f"{report}_{date.today().isoformat()}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/pdf")
def export_pdf(
    report: str = Query("fee_head_wise"),
    fy_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.EXPORT_REPORTS)),
):
    title, headers, rows, filter_desc = _build_export_data(report, db, fy_id, start_date, end_date)
    pdf_bytes = generate_report_pdf(title, headers, [[str(v) if v is not None else "" for v in row] for row in rows], filter_desc)
    filename = f"{report}_{date.today().isoformat()}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
