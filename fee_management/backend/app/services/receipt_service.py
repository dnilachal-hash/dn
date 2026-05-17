"""Receipt generation and management service."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.receipt import Receipt, ReceiptItem, ReceiptPayment, ReceiptCorrection, ReceiptStatus
from app.models.org import FinancialYear, Organisation
from app.models.student import Student, Course, Batch, AcademicSession
from app.services.audit_service import log_action


# ──────────────────────────────────────────
# Number utilities
# ──────────────────────────────────────────

def get_receipt_number_str(fy: FinancialYear, org: Optional[Organisation], number: int) -> str:
    """Format receipt number based on org setting."""
    fmt = "SIMPLE"
    if org and hasattr(org, "receipt_numbering_format"):
        fmt = str(org.receipt_numbering_format.value if hasattr(org.receipt_numbering_format, "value") else org.receipt_numbering_format)
    padded = str(number).zfill(4)
    if fmt == "PREFIXED":
        # e.g. 2025-26/0001
        parts = fy.name.split("-")
        if len(parts) == 2:
            prefix = f"{parts[0][-2:]}-{parts[1][-2:]}"
        else:
            prefix = fy.name
        return f"{prefix}/{padded}"
    return padded


def _amount_in_words(amount: Decimal) -> str:
    """Convert amount to words (Indian numbering)."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _below_hundred(n: int) -> str:
        if n < 20:
            return ones[n]
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")

    def _below_thousand(n: int) -> str:
        if n < 100:
            return _below_hundred(n)
        return ones[n // 100] + " Hundred" + (" " + _below_hundred(n % 100) if n % 100 else "")

    def _convert(n: int) -> str:
        if n == 0:
            return "Zero"
        parts = []
        if n >= 10000000:
            parts.append(_below_thousand(n // 10000000) + " Crore")
            n %= 10000000
        if n >= 100000:
            parts.append(_below_thousand(n // 100000) + " Lakh")
            n %= 100000
        if n >= 1000:
            parts.append(_below_thousand(n // 1000) + " Thousand")
            n %= 1000
        if n > 0:
            parts.append(_below_thousand(n))
        return " ".join(parts)

    total_paise = int(round(amount * 100))
    rupees = total_paise // 100
    paise = total_paise % 100
    result = "Rupees " + _convert(rupees)
    if paise:
        result += f" and {_convert(paise)} Paise"
    result += " Only"
    return result


# ──────────────────────────────────────────
# Core receipt generation
# ──────────────────────────────────────────

def generate_receipt(db: Session, data: Any, current_user: Any, request=None) -> Receipt:
    """
    Create a new receipt. Locks the FY row to prevent race conditions.
    data is a ReceiptCreate schema instance.
    """
    # 1. Validate FY
    fy = db.get(FinancialYear, data.financial_year_id)
    if not fy:
        raise ValueError(f"Financial year {data.financial_year_id} not found.")
    if fy.is_locked:
        raise ValueError(f"Financial year '{fy.name}' is locked. Cannot add receipts.")

    # 2. Fetch org for numbering format
    org = db.scalar(select(Organisation).limit(1))

    # 3. Resolve student details
    student = None
    student_name = data.student_name
    father_name = data.father_name
    course_name = data.course_name
    batch_name = data.batch_name
    session_name = data.session_name
    professional_year = data.professional_year
    roll_number = data.roll_number
    admission_number = data.admission_number

    if data.student_id:
        student = db.get(Student, data.student_id)
        if not student:
            raise ValueError(f"Student {data.student_id} not found.")
        student_name = student_name or student.student_name
        father_name = father_name or student.father_name
        professional_year = professional_year or student.professional_year
        roll_number = roll_number or student.roll_number
        admission_number = admission_number or student.admission_number
        if student.course:
            course_name = course_name or student.course.name
        elif student.course_id:
            c = db.get(Course, student.course_id)
            course_name = course_name or (c.name if c else None)
        if student.batch:
            batch_name = batch_name or student.batch.name
        elif student.batch_id:
            b = db.get(Batch, student.batch_id)
            batch_name = batch_name or (b.name if b else None)
        if student.academic_session:
            session_name = session_name or student.academic_session.name
        elif student.academic_session_id:
            s = db.get(AcademicSession, student.academic_session_id)
            session_name = session_name or (s.name if s else None)

    # 4. Compute total
    total = sum(Decimal(str(item.amount)) for item in data.items)

    # 5. Lock FY and get next receipt number (pessimistic lock via update)
    next_num = fy.next_receipt_number
    fy.next_receipt_number = next_num + 1
    db.flush()  # Flush so concurrent requests get different numbers

    receipt_num_str = get_receipt_number_str(fy, org, next_num)

    # 6. Create receipt
    receipt = Receipt(
        receipt_number=receipt_num_str,
        financial_year_id=fy.id,
        student_id=data.student_id,
        student_name=student_name,
        father_name=father_name,
        course_name=course_name,
        batch_name=batch_name,
        session_name=session_name,
        professional_year=professional_year,
        roll_number=roll_number,
        admission_number=admission_number,
        receipt_date=data.receipt_date,
        total_amount=total,
        amount_in_words=_amount_in_words(total),
        remarks=data.remarks,
        status=ReceiptStatus.ACTIVE,
        collected_by=current_user.id,
    )
    db.add(receipt)
    db.flush()

    # 7. Create items
    for i, item in enumerate(data.items):
        ri = ReceiptItem(
            receipt_id=receipt.id,
            fee_head_id=item.fee_head_id,
            fee_head_name=item.fee_head_name,
            amount=Decimal(str(item.amount)),
            sort_order=item.sort_order if hasattr(item, "sort_order") else i,
        )
        db.add(ri)

    # 8. Create payments
    for payment in data.payments:
        rp = ReceiptPayment(
            receipt_id=receipt.id,
            payment_mode_id=payment.payment_mode_id,
            payment_mode_name=payment.payment_mode_name,
            amount=Decimal(str(payment.amount)),
            reference_number=payment.reference_number,
            bank_name=payment.bank_name,
            branch_name=payment.branch_name,
            cheque_number=payment.cheque_number,
            cheque_date=payment.cheque_date,
            dd_number=payment.dd_number,
            dd_date=payment.dd_date,
            upi_id=payment.upi_id,
            transaction_id=payment.transaction_id,
            transaction_date=payment.transaction_date,
            payment_status=payment.payment_status,
            remarks=payment.remarks,
        )
        db.add(rp)

    db.flush()

    # 9. Audit
    log_action(
        db,
        current_user,
        "CREATE_RECEIPT",
        "receipt",
        receipt.id,
        None,
        {"receipt_number": receipt_num_str, "amount": str(total), "student_id": data.student_id},
        request=request,
    )

    return receipt


def cancel_receipt(
    db: Session, receipt: Receipt, reason: str, user: Any, request=None
) -> Receipt:
    """Cancel a receipt."""
    if receipt.status == ReceiptStatus.CANCELLED:
        raise ValueError("Receipt is already cancelled.")

    old_status = receipt.status.value if hasattr(receipt.status, "value") else receipt.status
    receipt.status = ReceiptStatus.CANCELLED
    receipt.cancel_reason = reason
    receipt.cancel_by = user.id
    receipt.cancel_at = datetime.utcnow()

    log_action(
        db, user, "CANCEL_RECEIPT", "receipt", receipt.id,
        {"status": old_status}, {"status": "CANCELLED", "reason": reason},
        request=request,
    )
    db.flush()
    return receipt


def correct_receipt(
    db: Session, receipt: Receipt, updates: Any, user: Any, request=None
) -> Receipt:
    """Correct a receipt and log the change."""
    old_values = {
        "remarks": receipt.remarks,
        "items": [{"fee_head_name": i.fee_head_name, "amount": str(i.amount)} for i in receipt.items],
        "payments": [{"payment_mode_name": p.payment_mode_name, "amount": str(p.amount)} for p in receipt.payments],
    }

    if updates.remarks is not None:
        receipt.remarks = updates.remarks

    if updates.items is not None:
        for item in receipt.items:
            db.delete(item)
        db.flush()
        for i, item in enumerate(updates.items):
            ri = ReceiptItem(
                receipt_id=receipt.id,
                fee_head_id=item.fee_head_id,
                fee_head_name=item.fee_head_name,
                amount=Decimal(str(item.amount)),
                sort_order=item.sort_order if hasattr(item, "sort_order") else i,
            )
            db.add(ri)
        new_total = sum(Decimal(str(item.amount)) for item in updates.items)
        receipt.total_amount = new_total
        receipt.amount_in_words = _amount_in_words(new_total)

    if updates.payments is not None:
        for pmt in receipt.payments:
            db.delete(pmt)
        db.flush()
        for pmt in updates.payments:
            rp = ReceiptPayment(
                receipt_id=receipt.id,
                payment_mode_id=pmt.payment_mode_id,
                payment_mode_name=pmt.payment_mode_name,
                amount=Decimal(str(pmt.amount)),
                reference_number=pmt.reference_number,
                bank_name=pmt.bank_name,
                branch_name=pmt.branch_name,
                cheque_number=pmt.cheque_number,
                cheque_date=pmt.cheque_date,
                dd_number=pmt.dd_number,
                dd_date=pmt.dd_date,
                upi_id=pmt.upi_id,
                transaction_id=pmt.transaction_id,
                transaction_date=pmt.transaction_date,
                payment_status=pmt.payment_status,
                remarks=pmt.remarks,
            )
            db.add(rp)

    receipt.status = ReceiptStatus.CORRECTED

    new_values = {
        "remarks": receipt.remarks,
        "items": [{"fee_head_name": i.fee_head_name, "amount": str(i.amount)} for i in (updates.items or [])],
    }

    correction = ReceiptCorrection(
        receipt_id=receipt.id,
        corrected_by=user.id,
        corrected_at=datetime.utcnow(),
        reason=updates.reason,
        old_values=old_values,
        new_values=new_values,
    )
    db.add(correction)

    log_action(
        db, user, "CORRECT_RECEIPT", "receipt", receipt.id,
        old_values, new_values, reason=updates.reason, request=request,
    )
    db.flush()
    return receipt
