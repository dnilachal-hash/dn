"""Bulk receipt upload service."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.receipt import (
    BulkUploadSession, BulkUploadRow, BulkUploadStatus, BulkRowStatus,
    Receipt, ReceiptItem, ReceiptPayment, ReceiptStatus,
)
from app.models.org import FinancialYear
from app.models.student import Student
from app.services.audit_service import log_action
from app.services.receipt_service import _amount_in_words, get_receipt_number_str


def parse_and_validate(file_bytes: bytes, db: Session, user: Any, filename: str = "upload.xlsx") -> BulkUploadSession:
    """Parse Excel, validate rows, create BulkUploadSession with rows. Does NOT commit receipts."""
    from app.services.excel_service import parse_bulk_upload_excel

    valid_rows, error_rows = parse_bulk_upload_excel(file_bytes, db)
    all_rows = valid_rows + error_rows

    session = BulkUploadSession(
        file_name=filename,
        uploaded_by=user.id,
        uploaded_at=datetime.utcnow(),
        total_rows=len(all_rows),
        success_rows=len(valid_rows),
        failed_rows=len(error_rows),
        duplicate_rows=sum(1 for r in error_rows if r.get("status") == "DUPLICATE"),
        status=BulkUploadStatus.PENDING,
    )
    db.add(session)
    db.flush()

    for row_info in all_rows:
        row = BulkUploadRow(
            session_id=session.id,
            row_number=row_info["row_number"],
            raw_data=row_info.get("raw_data"),
            parsed_data=row_info.get("parsed_data"),
            status=BulkRowStatus(row_info["status"]),
            error_message=row_info.get("error_message"),
        )
        db.add(row)

    db.flush()
    log_action(db, user, "BULK_UPLOAD_PARSED", "bulk_upload_session", session.id,
               None, {"file": filename, "total": len(all_rows), "success": len(valid_rows)})
    return session


def commit_upload(db: Session, session_id: int, user: Any, request=None) -> BulkUploadSession:
    """Commit all SUCCESS rows as receipts."""
    session = db.get(BulkUploadSession, session_id)
    if not session:
        raise ValueError("Bulk upload session not found.")
    if session.status not in (BulkUploadStatus.PENDING,):
        raise ValueError(f"Session status is '{session.status.value}'. Only PENDING sessions can be committed.")

    session.status = BulkUploadStatus.PROCESSING
    db.flush()

    from app.models.org import Organisation
    from sqlalchemy import select
    org = db.scalar(select(Organisation).limit(1))

    rows = list(db.execute(
        select(BulkUploadRow).where(
            BulkUploadRow.session_id == session_id,
            BulkUploadRow.status == BulkRowStatus.SUCCESS,
        )
    ).scalars())

    # Determine FY from first valid row or session
    fy = None
    if session.financial_year_id:
        fy = db.get(FinancialYear, session.financial_year_id)
    if not fy:
        fy = db.scalar(select(FinancialYear).where(FinancialYear.is_active == True))
    if not fy:
        raise ValueError("No active financial year found for import.")
    if fy.is_locked:
        raise ValueError(f"Financial year '{fy.name}' is locked.")

    success_count = 0
    failed_count = 0

    for row in rows:
        parsed = row.parsed_data
        if not parsed:
            row.status = BulkRowStatus.FAILED
            row.error_message = "No parsed data"
            failed_count += 1
            continue

        try:
            # Find student by admission number
            adm_no = parsed.get("admission_number")
            student = db.scalar(
                select(Student).where(Student.admission_number == adm_no)
            ) if adm_no else None

            receipt_date_str = parsed.get("receipt_date")
            if receipt_date_str:
                receipt_date = date.fromisoformat(receipt_date_str)
            else:
                receipt_date = date.today()

            # Build items
            items_data = parsed.get("items", [])
            total = sum(Decimal(str(item["amount"])) for item in items_data)

            # Get receipt number
            next_num = fy.next_receipt_number
            fy.next_receipt_number = next_num + 1
            db.flush()
            receipt_num_str = get_receipt_number_str(fy, org, next_num)

            receipt = Receipt(
                receipt_number=receipt_num_str,
                financial_year_id=fy.id,
                student_id=student.id if student else None,
                student_name=parsed.get("student_name") or (student.student_name if student else None),
                father_name=parsed.get("father_name") or (student.father_name if student else None),
                course_name=parsed.get("course_name"),
                batch_name=parsed.get("batch_name"),
                session_name=parsed.get("session_name"),
                professional_year=parsed.get("professional_year"),
                roll_number=parsed.get("roll_number"),
                admission_number=adm_no,
                receipt_date=receipt_date,
                total_amount=total,
                amount_in_words=_amount_in_words(total),
                remarks=parsed.get("remarks"),
                status=ReceiptStatus.IMPORTED,
                collected_by=user.id,
                imported_from=str(session_id),
            )
            db.add(receipt)
            db.flush()

            for i, item in enumerate(items_data):
                ri = ReceiptItem(
                    receipt_id=receipt.id,
                    fee_head_name=item["fee_head_name"],
                    amount=Decimal(str(item["amount"])),
                    sort_order=i,
                )
                db.add(ri)

            for pmt in parsed.get("payments", []):
                rp = ReceiptPayment(
                    receipt_id=receipt.id,
                    payment_mode_name=pmt["payment_mode_name"],
                    amount=Decimal(str(pmt["amount"])),
                    reference_number=pmt.get("reference_number"),
                    bank_name=pmt.get("bank_name"),
                    payment_status=pmt.get("payment_status", "CLEARED"),
                )
                db.add(rp)

            db.flush()
            row.receipt_id = receipt.id
            row.status = BulkRowStatus.SUCCESS
            success_count += 1

        except Exception as e:
            row.status = BulkRowStatus.FAILED
            row.error_message = str(e)[:500]
            failed_count += 1
            db.flush()

    session.success_rows = success_count
    session.failed_rows = (session.failed_rows or 0) + failed_count
    session.status = BulkUploadStatus.COMPLETED
    db.flush()

    log_action(db, user, "BULK_UPLOAD_COMMITTED", "bulk_upload_session", session_id,
               None, {"success": success_count, "failed": failed_count}, request=request)
    return session


def rollback_upload(db: Session, session_id: int, user: Any, request=None) -> BulkUploadSession:
    """Delete all receipts created in this upload session."""
    session = db.get(BulkUploadSession, session_id)
    if not session:
        raise ValueError("Bulk upload session not found.")
    if session.status == BulkUploadStatus.ROLLED_BACK:
        raise ValueError("Session has already been rolled back.")
    if session.status not in (BulkUploadStatus.COMPLETED, BulkUploadStatus.PROCESSING):
        raise ValueError(f"Cannot rollback session with status '{session.status.value}'.")

    rows_with_receipts = list(db.execute(
        select(BulkUploadRow).where(
            BulkUploadRow.session_id == session_id,
            BulkUploadRow.receipt_id.isnot(None),
        )
    ).scalars())

    deleted = 0
    for row in rows_with_receipts:
        receipt = db.get(Receipt, row.receipt_id)
        if receipt:
            db.delete(receipt)
            deleted += 1
        row.receipt_id = None
        row.status = BulkRowStatus.SKIPPED

    session.status = BulkUploadStatus.ROLLED_BACK
    session.rollback_at = datetime.utcnow()
    session.rollback_by = user.id
    db.flush()

    log_action(db, user, "BULK_UPLOAD_ROLLED_BACK", "bulk_upload_session", session_id,
               None, {"deleted_receipts": deleted}, request=request)
    return session
