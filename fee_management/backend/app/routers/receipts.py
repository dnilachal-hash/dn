"""Receipts and bulk upload router."""
from datetime import date
from math import ceil
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse, Response
import io

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, require_role, Permission
from app.database import get_db
from app.models.receipt import (
    Receipt, ReceiptStatus, BulkUploadSession, BulkUploadRow,
)
from app.models.org import Organisation, FinancialYear
from app.schemas.receipt import (
    ReceiptCreate, ReceiptOut, ReceiptCancelRequest, ReceiptCorrection,
    BulkUploadSessionOut, BulkUploadRowOut,
)
from app.services.receipt_service import generate_receipt, cancel_receipt, correct_receipt
from app.services.audit_service import log_action
from app.services.pdf_service import generate_receipt_pdf
from app.services.excel_service import generate_bulk_upload_template
from app.services.bulk_upload_service import parse_and_validate, commit_upload, rollback_upload

router = APIRouter(tags=["receipts"])


def _to_receipt_out(r: Receipt, db: Session) -> ReceiptOut:
    out = ReceiptOut.model_validate(r)
    if r.financial_year:
        out.fy_name = r.financial_year.name
    elif r.financial_year_id:
        fy = db.get(FinancialYear, r.financial_year_id)
        out.fy_name = fy.name if fy else None
    if hasattr(r, "collector") and r.collector:
        out.collector_name = r.collector.full_name
    return out


# ──────────────────────────────────────────
# Receipts CRUD
# ──────────────────────────────────────────

@router.get("/receipts")
def list_receipts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    fy_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    receipt_status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    payment_mode: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_RECEIPTS)),
):
    q = select(Receipt)
    if fy_id:
        q = q.where(Receipt.financial_year_id == fy_id)
    if student_id:
        q = q.where(Receipt.student_id == student_id)
    if receipt_status:
        q = q.where(Receipt.status == receipt_status)
    if start_date:
        q = q.where(Receipt.receipt_date >= start_date)
    if end_date:
        q = q.where(Receipt.receipt_date <= end_date)
    if search:
        like = f"%{search}%"
        q = q.where(or_(
            Receipt.receipt_number.ilike(like),
            Receipt.student_name.ilike(like),
            Receipt.admission_number.ilike(like),
        ))
    if payment_mode:
        from app.models.receipt import ReceiptPayment
        q = q.join(ReceiptPayment, ReceiptPayment.receipt_id == Receipt.id).where(
            ReceiptPayment.payment_mode_name == payment_mode
        ).distinct()

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    pages = ceil(total / page_size) if page_size else 1
    offset = (page - 1) * page_size

    receipts = list(db.execute(
        q.order_by(Receipt.receipt_date.desc(), Receipt.id.desc()).offset(offset).limit(page_size)
    ).scalars())

    return {
        "items": [_to_receipt_out(r, db) for r in receipts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("/receipts", response_model=ReceiptOut, status_code=201)
def create_receipt(
    payload: ReceiptCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.COLLECT_FEES)),
):
    try:
        receipt = generate_receipt(db, payload, current_user, request)
        db.commit()
        db.refresh(receipt)
        return _to_receipt_out(receipt, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/receipts/{receipt_id}", response_model=ReceiptOut)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_RECEIPTS)),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return _to_receipt_out(r, db)


@router.get("/receipts/{receipt_id}/pdf")
def get_receipt_pdf(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_RECEIPTS)),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")

    org = db.scalar(select(Organisation).limit(1))
    pdf_bytes = generate_receipt_pdf(r, org)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=receipt_{r.receipt_number}.pdf"},
    )


@router.put("/receipts/{receipt_id}", response_model=ReceiptOut)
def update_receipt(
    receipt_id: int,
    payload: ReceiptCorrection,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("super_admin")),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    if r.status == ReceiptStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot correct a cancelled receipt")
    try:
        r = correct_receipt(db, r, payload, current_user, request)
        db.commit()
        db.refresh(r)
        return _to_receipt_out(r, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/receipts/{receipt_id}/cancel", response_model=ReceiptOut)
def cancel_receipt_endpoint(
    receipt_id: int,
    payload: ReceiptCancelRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.CANCEL_RECEIPTS)),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    try:
        r = cancel_receipt(db, r, payload.reason, current_user, request)
        db.commit()
        db.refresh(r)
        return _to_receipt_out(r, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/receipts/{receipt_id}/reprint", response_model=ReceiptOut)
def reprint_receipt(
    receipt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_RECEIPTS)),
):
    r = db.get(Receipt, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    r.is_duplicate_print = True
    log_action(db, current_user, "REPRINT_RECEIPT", "receipt", receipt_id, request=request)
    db.commit()
    return _to_receipt_out(r, db)


# ──────────────────────────────────────────
# Bulk Upload
# ──────────────────────────────────────────

@router.get("/bulk-upload/template")
def download_template(current_user=Depends(require_permission(Permission.BULK_UPLOAD))):
    template_bytes = generate_bulk_upload_template()
    return Response(
        content=template_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bulk_receipt_template.xlsx"},
    )


@router.post("/bulk-upload", response_model=BulkUploadSessionOut, status_code=201)
async def bulk_upload_preview(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BULK_UPLOAD)),
):
    content = await file.read()
    try:
        session = parse_and_validate(content, db, current_user, filename=file.filename or "upload.xlsx")
        db.commit()
        return BulkUploadSessionOut.model_validate(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-upload/{session_id}/commit", response_model=BulkUploadSessionOut)
def bulk_upload_commit(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BULK_UPLOAD)),
):
    try:
        session = commit_upload(db, session_id, current_user, request)
        db.commit()
        return BulkUploadSessionOut.model_validate(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-upload/{session_id}/rollback", response_model=BulkUploadSessionOut)
def bulk_upload_rollback(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.ROLLBACK_UPLOAD)),
):
    try:
        session = rollback_upload(db, session_id, current_user, request)
        db.commit()
        return BulkUploadSessionOut.model_validate(session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bulk-upload", response_model=List[BulkUploadSessionOut])
def list_bulk_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BULK_UPLOAD)),
):
    sessions = list(db.execute(
        select(BulkUploadSession).order_by(BulkUploadSession.uploaded_at.desc()).limit(100)
    ).scalars())
    return [BulkUploadSessionOut.model_validate(s) for s in sessions]


@router.get("/bulk-upload/{session_id}/rows", response_model=List[BulkUploadRowOut])
def get_bulk_rows(
    session_id: int,
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.BULK_UPLOAD)),
):
    q = select(BulkUploadRow).where(BulkUploadRow.session_id == session_id).order_by(BulkUploadRow.row_number)
    if status_filter:
        q = q.where(BulkUploadRow.status == status_filter)
    rows = list(db.execute(q).scalars())
    return [BulkUploadRowOut.model_validate(r) for r in rows]
