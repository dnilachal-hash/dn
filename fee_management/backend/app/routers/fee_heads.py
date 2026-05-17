"""Fee heads and fee structures router."""
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, Permission
from app.database import get_db
from app.models.fee import (
    FeeHead, FeeStructure, FeeStructureItem,
    StudentFeeAssignment, StudentFeeOverride,
)
from app.models.student import Course, Batch, AcademicSession
from app.models.org import FinancialYear
from app.schemas.fee import (
    FeeHeadCreate, FeeHeadOut, FeeHeadUpdate,
    FeeStructureCreate, FeeStructureOut, FeeStructureItemOut, FeeStructureUpdate,
    StudentFeeOverrideCreate, StudentFeeOverrideOut,
)
from app.services.audit_service import log_action

router = APIRouter(tags=["fee"])


# ──────────────────────────────────────────
# Fee Heads
# ──────────────────────────────────────────

@router.get("/fee-heads", response_model=List[FeeHeadOut])
def list_fee_heads(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_FEE_HEADS)),
):
    q = select(FeeHead).order_by(FeeHead.sort_order, FeeHead.name)
    if active_only:
        q = q.where(FeeHead.is_active == True)
    return [FeeHeadOut.model_validate(f) for f in db.execute(q).scalars()]


@router.post("/fee-heads", response_model=FeeHeadOut, status_code=201)
def create_fee_head(
    payload: FeeHeadCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_HEADS)),
):
    existing = db.scalar(select(FeeHead).where(FeeHead.code == payload.code))
    if existing:
        raise HTTPException(status_code=400, detail=f"Fee head code '{payload.code}' exists")
    fh = FeeHead(**payload.model_dump())
    db.add(fh)
    db.flush()
    log_action(db, current_user, "CREATE_FEE_HEAD", "fee_head", fh.id, request=request)
    db.commit()
    return FeeHeadOut.model_validate(fh)


@router.get("/fee-heads/{fh_id}", response_model=FeeHeadOut)
def get_fee_head(fh_id: int, db: Session = Depends(get_db),
                 current_user=Depends(require_permission(Permission.VIEW_FEE_HEADS))):
    fh = db.get(FeeHead, fh_id)
    if not fh:
        raise HTTPException(status_code=404, detail="Fee head not found")
    return FeeHeadOut.model_validate(fh)


@router.put("/fee-heads/{fh_id}", response_model=FeeHeadOut)
def update_fee_head(
    fh_id: int,
    payload: FeeHeadUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_HEADS)),
):
    fh = db.get(FeeHead, fh_id)
    if not fh:
        raise HTTPException(status_code=404, detail="Fee head not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(fh, k, v)
    log_action(db, current_user, "UPDATE_FEE_HEAD", "fee_head", fh_id, request=request)
    db.commit()
    return FeeHeadOut.model_validate(fh)


@router.delete("/fee-heads/{fh_id}", status_code=204)
def delete_fee_head(fh_id: int, db: Session = Depends(get_db),
                    current_user=Depends(require_permission(Permission.MANAGE_FEE_HEADS))):
    fh = db.get(FeeHead, fh_id)
    if not fh:
        raise HTTPException(status_code=404, detail="Fee head not found")
    fh.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Fee Structures
# ──────────────────────────────────────────

def _enrich_structure(fs: FeeStructure, db: Session) -> FeeStructureOut:
    out = FeeStructureOut.model_validate(fs)
    out.items = []
    for item in fs.items:
        item_out = FeeStructureItemOut.model_validate(item)
        if item.fee_head:
            item_out.fee_head_name = item.fee_head.name
        elif item.fee_head_id:
            fh = db.get(FeeHead, item.fee_head_id)
            item_out.fee_head_name = fh.name if fh else None
        out.items.append(item_out)
    if fs.course_id:
        c = db.get(Course, fs.course_id)
        out.course_name = c.name if c else None
    if fs.batch_id:
        b = db.get(Batch, fs.batch_id)
        out.batch_name = b.name if b else None
    if fs.financial_year_id:
        fy = db.get(FinancialYear, fs.financial_year_id)
        out.fy_name = fy.name if fy else None
    out.total_amount = sum(Decimal(str(i.amount)) for i in fs.items)
    return out


@router.get("/fee-structures", response_model=List[FeeStructureOut])
def list_fee_structures(
    course_id: Optional[int] = None,
    fy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_FEE_STRUCTURES)),
):
    q = select(FeeStructure).order_by(FeeStructure.created_at.desc())
    if course_id:
        q = q.where(FeeStructure.course_id == course_id)
    if fy_id:
        q = q.where(FeeStructure.financial_year_id == fy_id)
    return [_enrich_structure(fs, db) for fs in db.execute(q).scalars()]


@router.post("/fee-structures", response_model=FeeStructureOut, status_code=201)
def create_fee_structure(
    payload: FeeStructureCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_STRUCTURES)),
):
    fs = FeeStructure(
        name=payload.name,
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        academic_session_id=payload.academic_session_id,
        financial_year_id=payload.financial_year_id,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(fs)
    db.flush()

    for i, item in enumerate(payload.items):
        fi = FeeStructureItem(
            fee_structure_id=fs.id,
            fee_head_id=item.fee_head_id,
            amount=item.amount,
            is_compulsory=item.is_compulsory,
            sort_order=item.sort_order or i,
        )
        db.add(fi)

    db.flush()
    log_action(db, current_user, "CREATE_FEE_STRUCTURE", "fee_structure", fs.id, request=request)
    db.commit()
    db.refresh(fs)
    return _enrich_structure(fs, db)


@router.get("/fee-structures/{fs_id}", response_model=FeeStructureOut)
def get_fee_structure(
    fs_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_FEE_STRUCTURES)),
):
    fs = db.get(FeeStructure, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    return _enrich_structure(fs, db)


@router.put("/fee-structures/{fs_id}", response_model=FeeStructureOut)
def update_fee_structure(
    fs_id: int,
    payload: FeeStructureUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_STRUCTURES)),
):
    fs = db.get(FeeStructure, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    if fs.is_frozen:
        raise HTTPException(status_code=400, detail="Cannot edit a frozen fee structure")

    if payload.name is not None:
        fs.name = payload.name
    if payload.is_active is not None:
        fs.is_active = payload.is_active
    if payload.is_frozen is not None:
        fs.is_frozen = payload.is_frozen

    if payload.items is not None:
        for item in fs.items:
            db.delete(item)
        db.flush()
        for i, item in enumerate(payload.items):
            fi = FeeStructureItem(
                fee_structure_id=fs.id,
                fee_head_id=item.fee_head_id,
                amount=item.amount,
                is_compulsory=item.is_compulsory,
                sort_order=item.sort_order or i,
            )
            db.add(fi)

    db.flush()
    log_action(db, current_user, "UPDATE_FEE_STRUCTURE", "fee_structure", fs_id, request=request)
    db.commit()
    db.refresh(fs)
    return _enrich_structure(fs, db)


@router.delete("/fee-structures/{fs_id}", status_code=204)
def delete_fee_structure(
    fs_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_STRUCTURES)),
):
    fs = db.get(FeeStructure, fs_id)
    if not fs:
        raise HTTPException(status_code=404, detail="Fee structure not found")
    if fs.is_frozen:
        raise HTTPException(status_code=400, detail="Cannot delete a frozen fee structure")
    fs.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Student fee assignments
# ──────────────────────────────────────────

@router.post("/students/{student_id}/fee-assignments")
def assign_fee_structure(
    student_id: int,
    fee_structure_id: int,
    financial_year_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_STRUCTURES)),
):
    from app.models.student import Student
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Deactivate existing
    existing = list(db.execute(
        select(StudentFeeAssignment).where(
            StudentFeeAssignment.student_id == student_id,
            StudentFeeAssignment.financial_year_id == financial_year_id,
            StudentFeeAssignment.is_active == True,
        )
    ).scalars())
    for a in existing:
        a.is_active = False

    asgn = StudentFeeAssignment(
        student_id=student_id,
        fee_structure_id=fee_structure_id,
        financial_year_id=financial_year_id,
        assigned_by=current_user.id,
        is_active=True,
    )
    db.add(asgn)
    log_action(db, current_user, "ASSIGN_FEE_STRUCTURE", "student_fee_assignment", student_id, request=request)
    db.commit()
    return {"message": "Fee structure assigned", "assignment_id": asgn.id}


@router.post("/fee-overrides", response_model=StudentFeeOverrideOut, status_code=201)
def create_fee_override(
    payload: StudentFeeOverrideCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FEE_STRUCTURES)),
):
    override = StudentFeeOverride(**payload.model_dump(), created_by=current_user.id)
    db.add(override)
    db.flush()
    log_action(db, current_user, "CREATE_FEE_OVERRIDE", "student_fee_override", override.id, request=request)
    db.commit()
    return StudentFeeOverrideOut.model_validate(override)
