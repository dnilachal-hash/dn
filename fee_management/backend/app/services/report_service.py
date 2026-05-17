"""Report data generation service — returns dicts/lists (not files)."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, and_, extract, or_
from sqlalchemy.orm import Session, joinedload

from app.models.receipt import Receipt, ReceiptItem, ReceiptPayment, ReceiptStatus, PaymentStatus
from app.models.student import Student, Course, Batch, AcademicSession
from app.models.org import FinancialYear
from app.models.fee import FeeHead, FeeStructure, FeeStructureItem, StudentFeeAssignment, StudentFeeOverride


def _dec(v) -> Decimal:
    if v is None:
        return Decimal("0")
    return Decimal(str(v))


# ──────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────

def dashboard_stats(db: Session, user=None) -> dict:
    today = date.today()
    month_start = today.replace(day=1)

    active_fy = db.scalar(select(FinancialYear).where(FinancialYear.is_active == True))

    def _sum(conditions):
        q = select(func.coalesce(func.sum(Receipt.total_amount), 0)).where(
            Receipt.status != ReceiptStatus.CANCELLED, *conditions
        )
        return _dec(db.scalar(q))

    def _count(conditions):
        q = select(func.count(Receipt.id)).where(
            Receipt.status != ReceiptStatus.CANCELLED, *conditions
        )
        return db.scalar(q) or 0

    today_col = _sum([Receipt.receipt_date == today])
    month_col = _sum([Receipt.receipt_date >= month_start])
    fy_col = _sum([Receipt.financial_year_id == active_fy.id] if active_fy else [])

    today_cnt = _count([Receipt.receipt_date == today])
    month_cnt = _count([Receipt.receipt_date >= month_start])
    fy_cnt = _count([Receipt.financial_year_id == active_fy.id] if active_fy else [])

    # By mode
    mode_q = (
        select(ReceiptPayment.payment_mode_name, func.coalesce(func.sum(ReceiptPayment.amount), 0))
        .join(Receipt, Receipt.id == ReceiptPayment.receipt_id)
        .where(
            Receipt.status != ReceiptStatus.CANCELLED,
            Receipt.receipt_date >= month_start,
        )
        .group_by(ReceiptPayment.payment_mode_name)
    )
    by_mode = {row[0]: _dec(row[1]) for row in db.execute(mode_q).all()}

    pending_cheques = db.scalar(
        select(func.count(ReceiptPayment.id)).where(
            ReceiptPayment.payment_status == PaymentStatus.PENDING,
            ReceiptPayment.payment_mode_name == "CHEQUE",
        )
    ) or 0

    bounced_cheques = db.scalar(
        select(func.count(ReceiptPayment.id)).where(
            ReceiptPayment.payment_status == PaymentStatus.BOUNCED
        )
    ) or 0

    cancelled_today = db.scalar(
        select(func.count(Receipt.id)).where(
            Receipt.status == ReceiptStatus.CANCELLED,
            Receipt.cancel_at >= datetime.combine(today, datetime.min.time()),
        )
    ) or 0

    recent_q = (
        select(Receipt)
        .where(Receipt.status != ReceiptStatus.CANCELLED)
        .order_by(Receipt.created_at.desc())
        .limit(10)
    )
    recent = []
    for r in db.execute(recent_q).scalars():
        recent.append({
            "id": r.id,
            "receipt_number": r.receipt_number,
            "student_name": r.student_name,
            "amount": str(r.total_amount),
            "date": r.receipt_date.isoformat(),
            "status": r.status.value if hasattr(r.status, "value") else r.status,
        })

    active_students = db.scalar(select(func.count(Student.id)).where(Student.student_status == "ACTIVE")) or 0
    total_students = db.scalar(select(func.count(Student.id))) or 0

    return {
        "today_collection": today_col,
        "month_collection": month_col,
        "fy_collection": fy_col,
        "today_receipt_count": today_cnt,
        "month_receipt_count": month_cnt,
        "fy_receipt_count": fy_cnt,
        "collection_by_mode": by_mode,
        "pending_cheques": pending_cheques,
        "bounced_cheques": bounced_cheques,
        "cancelled_receipts_today": cancelled_today,
        "recent_receipts": recent,
        "active_students": active_students,
        "total_students": total_students,
    }


# ──────────────────────────────────────────
# Daily collection
# ──────────────────────────────────────────

def daily_collection(db: Session, for_date: date, filters: dict = None) -> dict:
    conds = [Receipt.receipt_date == for_date, Receipt.status != ReceiptStatus.CANCELLED]
    if filters and filters.get("fy_id"):
        conds.append(Receipt.financial_year_id == filters["fy_id"])

    receipts_q = select(Receipt).where(*conds).order_by(Receipt.receipt_number)
    receipts = list(db.execute(receipts_q).scalars())

    total = sum(_dec(r.total_amount) for r in receipts)

    # By fee head
    fh_q = (
        select(ReceiptItem.fee_head_name, func.sum(ReceiptItem.amount))
        .join(Receipt, Receipt.id == ReceiptItem.receipt_id)
        .where(*conds)
        .group_by(ReceiptItem.fee_head_name)
        .order_by(func.sum(ReceiptItem.amount).desc())
    )
    by_fh = [{"fee_head": row[0], "amount": _dec(row[1])} for row in db.execute(fh_q).all()]

    # By mode
    mode_q = (
        select(ReceiptPayment.payment_mode_name, func.sum(ReceiptPayment.amount))
        .join(Receipt, Receipt.id == ReceiptPayment.receipt_id)
        .where(*conds)
        .group_by(ReceiptPayment.payment_mode_name)
    )
    by_mode = [{"mode": row[0], "amount": _dec(row[1])} for row in db.execute(mode_q).all()]

    receipt_list = [{
        "id": r.id,
        "receipt_number": r.receipt_number,
        "student_name": r.student_name,
        "admission_number": r.admission_number,
        "amount": str(r.total_amount),
        "status": r.status.value if hasattr(r.status, "value") else r.status,
    } for r in receipts]

    return {
        "date": for_date,
        "total_amount": total,
        "receipt_count": len(receipts),
        "by_fee_head": by_fh,
        "by_payment_mode": by_mode,
        "receipts": receipt_list,
    }


# ──────────────────────────────────────────
# Monthly collection
# ──────────────────────────────────────────

def monthly_collection(db: Session, year: int, month: int, filters: dict = None) -> dict:
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    conds = [
        Receipt.receipt_date >= month_start,
        Receipt.receipt_date < month_end,
        Receipt.status != ReceiptStatus.CANCELLED,
    ]
    if filters and filters.get("fy_id"):
        conds.append(Receipt.financial_year_id == filters["fy_id"])

    total_q = select(func.coalesce(func.sum(Receipt.total_amount), 0)).where(*conds)
    total = _dec(db.scalar(total_q))
    count = db.scalar(select(func.count(Receipt.id)).where(*conds)) or 0

    # Daily breakdown
    daily_q = (
        select(Receipt.receipt_date, func.sum(Receipt.total_amount), func.count(Receipt.id))
        .where(*conds)
        .group_by(Receipt.receipt_date)
        .order_by(Receipt.receipt_date)
    )
    daily = [{"date": row[0].isoformat(), "amount": _dec(row[1]), "count": row[2]}
             for row in db.execute(daily_q).all()]

    fh_q = (
        select(ReceiptItem.fee_head_name, func.sum(ReceiptItem.amount))
        .join(Receipt, Receipt.id == ReceiptItem.receipt_id)
        .where(*conds)
        .group_by(ReceiptItem.fee_head_name)
        .order_by(func.sum(ReceiptItem.amount).desc())
    )
    by_fh = [{"fee_head": row[0], "amount": _dec(row[1])} for row in db.execute(fh_q).all()]

    return {
        "month": month,
        "year": year,
        "total_amount": total,
        "receipt_count": count,
        "by_fee_head": by_fh,
        "by_payment_mode": [],
        "receipts": daily,
    }


# ──────────────────────────────────────────
# FY summary
# ──────────────────────────────────────────

def fy_summary(db: Session, fy_id: int) -> dict:
    fy = db.get(FinancialYear, fy_id)
    if not fy:
        return {}
    conds = [Receipt.financial_year_id == fy_id, Receipt.status != ReceiptStatus.CANCELLED]
    total = _dec(db.scalar(select(func.coalesce(func.sum(Receipt.total_amount), 0)).where(*conds)))
    count = db.scalar(select(func.count(Receipt.id)).where(*conds)) or 0

    fh_q = (
        select(ReceiptItem.fee_head_name, func.sum(ReceiptItem.amount))
        .join(Receipt)
        .where(*conds)
        .group_by(ReceiptItem.fee_head_name)
        .order_by(func.sum(ReceiptItem.amount).desc())
    )
    by_fh = [{"fee_head": r[0], "amount": _dec(r[1])} for r in db.execute(fh_q).all()]

    mode_q = (
        select(ReceiptPayment.payment_mode_name, func.sum(ReceiptPayment.amount))
        .join(Receipt)
        .where(*conds)
        .group_by(ReceiptPayment.payment_mode_name)
    )
    by_mode = [{"mode": r[0], "amount": _dec(r[1])} for r in db.execute(mode_q).all()]

    return {
        "fy_id": fy_id,
        "fy_name": fy.name,
        "total_amount": total,
        "receipt_count": count,
        "by_fee_head": by_fh,
        "by_payment_mode": by_mode,
    }


# ──────────────────────────────────────────
# Student ledger
# ──────────────────────────────────────────

def student_ledger(db: Session, student_id: int, fy_id: Optional[int] = None) -> dict:
    student = db.get(Student, student_id)
    if not student:
        return {}

    conds = [Receipt.student_id == student_id, Receipt.status != ReceiptStatus.CANCELLED]
    if fy_id:
        conds.append(Receipt.financial_year_id == fy_id)

    receipts_q = select(Receipt).where(*conds).order_by(Receipt.receipt_date)
    receipts = list(db.execute(receipts_q).scalars())
    total_paid = sum(_dec(r.total_amount) for r in receipts)

    # Get assigned fees
    assign_conds = [StudentFeeAssignment.student_id == student_id, StudentFeeAssignment.is_active == True]
    if fy_id:
        assign_conds.append(StudentFeeAssignment.financial_year_id == fy_id)

    assignments = list(db.execute(select(StudentFeeAssignment).where(*assign_conds)).scalars())
    total_assigned = Decimal("0")
    by_fee_head = {}

    for asgn in assignments:
        structure = db.get(FeeStructure, asgn.fee_structure_id)
        if not structure:
            continue
        for item in structure.items:
            fh_name = item.fee_head.name if item.fee_head else f"FH-{item.fee_head_id}"
            # Check for override
            override = db.scalar(
                select(StudentFeeOverride).where(
                    StudentFeeOverride.student_id == student_id,
                    StudentFeeOverride.fee_head_id == item.fee_head_id,
                    StudentFeeOverride.financial_year_id == asgn.financial_year_id,
                )
            )
            amount = _dec(override.override_amount if override else item.amount)
            total_assigned += amount
            by_fee_head[fh_name] = by_fee_head.get(fh_name, Decimal("0")) + amount

    # Paid per fee head
    paid_fh_q = (
        select(ReceiptItem.fee_head_name, func.sum(ReceiptItem.amount))
        .join(Receipt)
        .where(*conds)
        .group_by(ReceiptItem.fee_head_name)
    )
    paid_fh = {row[0]: _dec(row[1]) for row in db.execute(paid_fh_q).all()}

    fh_summary = []
    all_fhs = set(list(by_fee_head.keys()) + list(paid_fh.keys()))
    for fh in all_fhs:
        assigned = by_fee_head.get(fh, Decimal("0"))
        paid = paid_fh.get(fh, Decimal("0"))
        fh_summary.append({
            "fee_head": fh,
            "assigned": assigned,
            "paid": paid,
            "balance": assigned - paid,
        })

    receipt_list = [{
        "id": r.id,
        "receipt_number": r.receipt_number,
        "date": r.receipt_date.isoformat(),
        "amount": str(r.total_amount),
        "status": r.status.value if hasattr(r.status, "value") else r.status,
        "items": [{"name": i.fee_head_name, "amount": str(i.amount)} for i in r.items],
    } for r in receipts]

    return {
        "student_id": student_id,
        "student_name": student.student_name,
        "admission_number": student.admission_number,
        "course_name": student.course.name if student.course else None,
        "batch_name": student.batch.name if student.batch else None,
        "receipts": receipt_list,
        "total_paid": total_paid,
        "total_assigned": total_assigned,
        "balance": total_assigned - total_paid,
        "by_fee_head": fh_summary,
    }


# ──────────────────────────────────────────
# Fee head wise
# ──────────────────────────────────────────

def fee_head_wise(db: Session, filters: dict = None) -> list:
    conds = [Receipt.status != ReceiptStatus.CANCELLED]
    if filters:
        if filters.get("fy_id"):
            conds.append(Receipt.financial_year_id == filters["fy_id"])
        if filters.get("start_date"):
            conds.append(Receipt.receipt_date >= filters["start_date"])
        if filters.get("end_date"):
            conds.append(Receipt.receipt_date <= filters["end_date"])

    q = (
        select(ReceiptItem.fee_head_name, func.sum(ReceiptItem.amount), func.count(ReceiptItem.id))
        .join(Receipt)
        .where(*conds)
        .group_by(ReceiptItem.fee_head_name)
        .order_by(func.sum(ReceiptItem.amount).desc())
    )
    return [{"fee_head": r[0], "total": _dec(r[1]), "count": r[2]} for r in db.execute(q).all()]


# ──────────────────────────────────────────
# Payment mode wise
# ──────────────────────────────────────────

def payment_mode_wise(db: Session, filters: dict = None) -> list:
    conds = [Receipt.status != ReceiptStatus.CANCELLED]
    if filters:
        if filters.get("fy_id"):
            conds.append(Receipt.financial_year_id == filters["fy_id"])
        if filters.get("start_date"):
            conds.append(Receipt.receipt_date >= filters["start_date"])
        if filters.get("end_date"):
            conds.append(Receipt.receipt_date <= filters["end_date"])

    q = (
        select(ReceiptPayment.payment_mode_name, func.sum(ReceiptPayment.amount), func.count(ReceiptPayment.id))
        .join(Receipt)
        .where(*conds)
        .group_by(ReceiptPayment.payment_mode_name)
        .order_by(func.sum(ReceiptPayment.amount).desc())
    )
    return [{"mode": r[0], "total": _dec(r[1]), "count": r[2]} for r in db.execute(q).all()]


# ──────────────────────────────────────────
# Dues report
# ──────────────────────────────────────────

def dues_report(db: Session, filters: dict = None) -> list:
    fy_id = filters.get("fy_id") if filters else None

    assign_conds = [StudentFeeAssignment.is_active == True]
    if fy_id:
        assign_conds.append(StudentFeeAssignment.financial_year_id == fy_id)

    assignments = list(db.execute(select(StudentFeeAssignment).where(*assign_conds)).scalars())

    student_dues = {}
    for asgn in assignments:
        sid = asgn.student_id
        if sid not in student_dues:
            student_dues[sid] = {"total_fees": Decimal("0"), "total_paid": Decimal("0")}
        structure = db.get(FeeStructure, asgn.fee_structure_id)
        if structure:
            for item in structure.items:
                override = db.scalar(
                    select(StudentFeeOverride).where(
                        StudentFeeOverride.student_id == sid,
                        StudentFeeOverride.fee_head_id == item.fee_head_id,
                        StudentFeeOverride.financial_year_id == asgn.financial_year_id,
                    )
                )
                student_dues[sid]["total_fees"] += _dec(
                    override.override_amount if override else item.amount
                )

    # Get paid amounts per student
    paid_conds = [Receipt.status != ReceiptStatus.CANCELLED]
    if fy_id:
        paid_conds.append(Receipt.financial_year_id == fy_id)

    paid_q = (
        select(Receipt.student_id, func.sum(Receipt.total_amount))
        .where(*paid_conds)
        .where(Receipt.student_id.isnot(None))
        .group_by(Receipt.student_id)
    )
    for row in db.execute(paid_q).all():
        sid, paid = row[0], _dec(row[1])
        if sid in student_dues:
            student_dues[sid]["total_paid"] = paid

    result = []
    for sid, dues in student_dues.items():
        balance = dues["total_fees"] - dues["total_paid"]
        if balance <= 0:
            continue
        student = db.get(Student, sid)
        if not student:
            continue
        result.append({
            "student_id": sid,
            "admission_number": student.admission_number,
            "student_name": student.student_name,
            "father_name": student.father_name,
            "course_name": student.course.name if student.course else None,
            "batch_name": student.batch.name if student.batch else None,
            "professional_year": student.professional_year,
            "total_fees": dues["total_fees"],
            "total_paid": dues["total_paid"],
            "balance": balance,
        })

    result.sort(key=lambda x: x["balance"], reverse=True)
    return result


# ──────────────────────────────────────────
# Cheque report
# ──────────────────────────────────────────

def cheque_report(db: Session, filters: dict = None) -> list:
    conds = [or_(
        ReceiptPayment.payment_mode_name == "CHEQUE",
        ReceiptPayment.payment_mode_name == "DD",
    )]
    if filters:
        if filters.get("status"):
            conds.append(ReceiptPayment.payment_status == filters["status"])
        if filters.get("start_date"):
            conds.append(ReceiptPayment.cheque_date >= filters["start_date"])
        if filters.get("end_date"):
            conds.append(ReceiptPayment.cheque_date <= filters["end_date"])

    q = (
        select(ReceiptPayment, Receipt)
        .join(Receipt, Receipt.id == ReceiptPayment.receipt_id)
        .where(*conds)
        .order_by(ReceiptPayment.cheque_date.desc().nullsfirst())
    )
    result = []
    for pmt, r in db.execute(q).all():
        result.append({
            "receipt_number": r.receipt_number,
            "receipt_date": r.receipt_date.isoformat() if r.receipt_date else None,
            "student_name": r.student_name,
            "mode": pmt.payment_mode_name,
            "amount": str(pmt.amount),
            "cheque_number": pmt.cheque_number or pmt.dd_number,
            "cheque_date": pmt.cheque_date.isoformat() if pmt.cheque_date else None,
            "bank_name": pmt.bank_name,
            "status": pmt.payment_status.value if hasattr(pmt.payment_status, "value") else pmt.payment_status,
            "clearance_date": pmt.clearance_date.isoformat() if pmt.clearance_date else None,
            "bounce_reason": pmt.bounce_reason,
        })
    return result


# ──────────────────────────────────────────
# Cancelled receipts
# ──────────────────────────────────────────

def cancelled_receipts(db: Session, filters: dict = None) -> list:
    conds = [Receipt.status == ReceiptStatus.CANCELLED]
    if filters:
        if filters.get("start_date"):
            conds.append(Receipt.receipt_date >= filters["start_date"])
        if filters.get("end_date"):
            conds.append(Receipt.receipt_date <= filters["end_date"])
        if filters.get("fy_id"):
            conds.append(Receipt.financial_year_id == filters["fy_id"])

    q = select(Receipt).where(*conds).order_by(Receipt.cancel_at.desc())
    result = []
    for r in db.execute(q).scalars():
        result.append({
            "id": r.id,
            "receipt_number": r.receipt_number,
            "student_name": r.student_name,
            "admission_number": r.admission_number,
            "amount": str(r.total_amount),
            "receipt_date": r.receipt_date.isoformat() if r.receipt_date else None,
            "cancel_reason": r.cancel_reason,
            "cancel_at": r.cancel_at.isoformat() if r.cancel_at else None,
        })
    return result


# ──────────────────────────────────────────
# Corrected receipts
# ──────────────────────────────────────────

def corrected_receipts(db: Session, filters: dict = None) -> list:
    from app.models.receipt import ReceiptCorrection
    conds = [Receipt.status == ReceiptStatus.CORRECTED]
    if filters:
        if filters.get("fy_id"):
            conds.append(Receipt.financial_year_id == filters["fy_id"])
        if filters.get("start_date"):
            conds.append(Receipt.receipt_date >= filters["start_date"])
        if filters.get("end_date"):
            conds.append(Receipt.receipt_date <= filters["end_date"])

    q = select(Receipt).where(*conds).order_by(Receipt.updated_at.desc())
    result = []
    for r in db.execute(q).scalars():
        corrections = sorted(r.corrections, key=lambda c: c.corrected_at, reverse=True)
        result.append({
            "id": r.id,
            "receipt_number": r.receipt_number,
            "student_name": r.student_name,
            "amount": str(r.total_amount),
            "receipt_date": r.receipt_date.isoformat() if r.receipt_date else None,
            "correction_count": len(corrections),
            "last_corrected_at": corrections[0].corrected_at.isoformat() if corrections else None,
            "last_reason": corrections[0].reason if corrections else None,
        })
    return result
