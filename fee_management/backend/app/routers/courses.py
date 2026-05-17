"""Courses, batches, sessions, categories, financial years, payment modes."""
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, Permission
from app.database import get_db
from app.models.student import Course, Batch, AcademicSession, StudentCategory
from app.models.org import FinancialYear, PaymentMode
from app.schemas.student import (
    CourseCreate, CourseOut, BatchCreate, BatchOut,
    SessionCreate, SessionOut, CategoryCreate, CategoryOut,
)
from app.schemas.receipt import (
    FinancialYearCreate, FinancialYearOut, PaymentModeCreate, PaymentModeOut,
)
from app.services.audit_service import log_action

router = APIRouter(tags=["courses"])


# ──────────────────────────────────────────
# Courses
# ──────────────────────────────────────────

@router.get("/courses", response_model=List[CourseOut])
def list_courses(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    return [CourseOut.model_validate(c) for c in db.execute(select(Course).order_by(Course.name)).scalars()]


@router.post("/courses", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    existing = db.scalar(select(Course).where(Course.code == payload.code))
    if existing:
        raise HTTPException(status_code=400, detail=f"Course code '{payload.code}' exists")
    course = Course(**payload.model_dump())
    db.add(course)
    db.flush()
    log_action(db, current_user, "CREATE_COURSE", "course", course.id, request=request)
    db.commit()
    return CourseOut.model_validate(course)


@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db),
               current_user=Depends(require_permission(Permission.VIEW_COURSES))):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseOut.model_validate(c)


@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int,
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    log_action(db, current_user, "UPDATE_COURSE", "course", course_id, request=request)
    db.commit()
    return CourseOut.model_validate(c)


@router.delete("/courses/{course_id}", status_code=204)
def delete_course(course_id: int, db: Session = Depends(get_db),
                  current_user=Depends(require_permission(Permission.MANAGE_COURSES))):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    c.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Batches
# ──────────────────────────────────────────

@router.get("/batches", response_model=List[BatchOut])
def list_batches(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    q = select(Batch).order_by(Batch.start_year.desc())
    if course_id:
        q = q.where(Batch.course_id == course_id)
    return [BatchOut.model_validate(b) for b in db.execute(q).scalars()]


@router.post("/batches", response_model=BatchOut, status_code=201)
def create_batch(
    payload: BatchCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    batch = Batch(**payload.model_dump())
    db.add(batch)
    db.flush()
    log_action(db, current_user, "CREATE_BATCH", "batch", batch.id, request=request)
    db.commit()
    return BatchOut.model_validate(batch)


@router.put("/batches/{batch_id}", response_model=BatchOut)
def update_batch(
    batch_id: int,
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    b = db.get(Batch, batch_id)
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(b, k, v)
    db.commit()
    return BatchOut.model_validate(b)


@router.delete("/batches/{batch_id}", status_code=204)
def delete_batch(batch_id: int, db: Session = Depends(get_db),
                 current_user=Depends(require_permission(Permission.MANAGE_COURSES))):
    b = db.get(Batch, batch_id)
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    b.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Academic Sessions
# ──────────────────────────────────────────

@router.get("/academic-sessions", response_model=List[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    return [SessionOut.model_validate(s) for s in db.execute(select(AcademicSession).order_by(AcademicSession.name.desc())).scalars()]


@router.post("/academic-sessions", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    existing = db.scalar(select(AcademicSession).where(AcademicSession.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail=f"Session '{payload.name}' already exists")
    sess = AcademicSession(**payload.model_dump())
    db.add(sess)
    db.flush()
    log_action(db, current_user, "CREATE_SESSION", "academic_session", sess.id, request=request)
    db.commit()
    return SessionOut.model_validate(sess)


@router.put("/academic-sessions/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    s = db.get(AcademicSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    db.commit()
    return SessionOut.model_validate(s)


@router.delete("/academic-sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db),
                   current_user=Depends(require_permission(Permission.MANAGE_COURSES))):
    s = db.get(AcademicSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Student Categories
# ──────────────────────────────────────────

@router.get("/student-categories", response_model=List[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    return [CategoryOut.model_validate(c) for c in db.execute(select(StudentCategory).order_by(StudentCategory.name)).scalars()]


@router.post("/student-categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    cat = StudentCategory(**payload.model_dump())
    db.add(cat)
    db.commit()
    return CategoryOut.model_validate(cat)


@router.put("/student-categories/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_COURSES)),
):
    c = db.get(StudentCategory, cat_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    db.commit()
    return CategoryOut.model_validate(c)


@router.delete("/student-categories/{cat_id}", status_code=204)
def delete_category(cat_id: int, db: Session = Depends(get_db),
                    current_user=Depends(require_permission(Permission.MANAGE_COURSES))):
    c = db.get(StudentCategory, cat_id)
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    c.is_active = False
    db.commit()


# ──────────────────────────────────────────
# Financial Years
# ──────────────────────────────────────────

@router.get("/financial-years", response_model=List[FinancialYearOut])
def list_fy(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    return [FinancialYearOut.model_validate(f) for f in db.execute(select(FinancialYear).order_by(FinancialYear.name.desc())).scalars()]


@router.post("/financial-years", response_model=FinancialYearOut, status_code=201)
def create_fy(
    payload: FinancialYearCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FINANCIAL_YEARS)),
):
    existing = db.scalar(select(FinancialYear).where(FinancialYear.name == payload.name))
    if existing:
        raise HTTPException(status_code=400, detail=f"Financial year '{payload.name}' exists")
    fy = FinancialYear(**payload.model_dump())
    db.add(fy)
    db.flush()
    log_action(db, current_user, "CREATE_FY", "financial_year", fy.id, request=request)
    db.commit()
    return FinancialYearOut.model_validate(fy)


@router.put("/financial-years/{fy_id}", response_model=FinancialYearOut)
def update_fy(
    fy_id: int,
    payload: FinancialYearCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FINANCIAL_YEARS)),
):
    fy = db.get(FinancialYear, fy_id)
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    old = {"is_locked": fy.is_locked, "is_active": fy.is_active}
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(fy, k, v)
    log_action(db, current_user, "UPDATE_FY", "financial_year", fy_id, old, request=request)
    db.commit()
    return FinancialYearOut.model_validate(fy)


@router.post("/financial-years/{fy_id}/lock", response_model=FinancialYearOut)
def lock_fy(
    fy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FINANCIAL_YEARS)),
):
    fy = db.get(FinancialYear, fy_id)
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    fy.is_locked = True
    log_action(db, current_user, "LOCK_FY", "financial_year", fy_id, request=request)
    db.commit()
    return FinancialYearOut.model_validate(fy)


@router.post("/financial-years/{fy_id}/unlock", response_model=FinancialYearOut)
def unlock_fy(
    fy_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_FINANCIAL_YEARS)),
):
    fy = db.get(FinancialYear, fy_id)
    if not fy:
        raise HTTPException(status_code=404, detail="Financial year not found")
    fy.is_locked = False
    log_action(db, current_user, "UNLOCK_FY", "financial_year", fy_id, request=request)
    db.commit()
    return FinancialYearOut.model_validate(fy)


# ──────────────────────────────────────────
# Payment Modes
# ──────────────────────────────────────────

@router.get("/payment-modes", response_model=List[PaymentModeOut])
def list_payment_modes(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_COURSES)),
):
    return [PaymentModeOut.model_validate(p) for p in db.execute(
        select(PaymentMode).order_by(PaymentMode.sort_order, PaymentMode.name)
    ).scalars()]


@router.post("/payment-modes", response_model=PaymentModeOut, status_code=201)
def create_payment_mode(
    payload: PaymentModeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_PAYMENT_MODES)),
):
    pm = PaymentMode(**payload.model_dump())
    db.add(pm)
    db.commit()
    return PaymentModeOut.model_validate(pm)


@router.put("/payment-modes/{pm_id}", response_model=PaymentModeOut)
def update_payment_mode(
    pm_id: int,
    payload: PaymentModeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_PAYMENT_MODES)),
):
    pm = db.get(PaymentMode, pm_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Payment mode not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(pm, k, v)
    db.commit()
    return PaymentModeOut.model_validate(pm)


@router.delete("/payment-modes/{pm_id}", status_code=204)
def delete_payment_mode(
    pm_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_PAYMENT_MODES)),
):
    pm = db.get(PaymentMode, pm_id)
    if not pm:
        raise HTTPException(status_code=404, detail="Payment mode not found")
    pm.is_active = False
    db.commit()
