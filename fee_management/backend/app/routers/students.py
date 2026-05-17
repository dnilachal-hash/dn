"""Student management router."""
import io
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.core.permissions import require_permission, Permission
from app.database import get_db
from app.models.student import Student, Course, Batch, AcademicSession, StudentCategory
from app.models.fee import StudentFeeAssignment, FeeStructure, FeeStructureItem, StudentFeeOverride
from app.models.receipt import Receipt, ReceiptItem, ReceiptStatus
from app.schemas.student import StudentCreate, StudentUpdate, StudentOut, StudentListOut
from app.services.audit_service import log_action
from decimal import Decimal
from sqlalchemy import select as sa_select

router = APIRouter(prefix="/students", tags=["students"])


def _enrich(student: Student, db: Session) -> StudentOut:
    out = StudentOut.model_validate(student)
    if student.course_id:
        c = db.get(Course, student.course_id)
        out.course_name = c.name if c else None
    if student.batch_id:
        b = db.get(Batch, student.batch_id)
        out.batch_name = b.name if b else None
    if student.academic_session_id:
        s = db.get(AcademicSession, student.academic_session_id)
        out.session_name = s.name if s else None
    if student.category_id:
        cat = db.get(StudentCategory, student.category_id)
        out.category_name = cat.name if cat else None
    return out


@router.get("", response_model=StudentListOut)
def list_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    batch_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    student_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_STUDENTS)),
):
    q = select(Student)
    if search:
        like = f"%{search}%"
        q = q.where(or_(
            Student.student_name.ilike(like),
            Student.admission_number.ilike(like),
            Student.roll_number.ilike(like),
            Student.mobile.ilike(like),
            Student.registration_number.ilike(like),
        ))
    if course_id:
        q = q.where(Student.course_id == course_id)
    if batch_id:
        q = q.where(Student.batch_id == batch_id)
    if session_id:
        q = q.where(Student.academic_session_id == session_id)
    if student_status:
        q = q.where(Student.student_status == student_status)

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    pages = ceil(total / page_size) if page_size else 1
    offset = (page - 1) * page_size

    students = list(db.execute(
        q.order_by(Student.student_name).offset(offset).limit(page_size)
    ).scalars())

    return StudentListOut(
        items=[_enrich(s, db) for s in students],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=StudentOut, status_code=201)
def create_student(
    payload: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_STUDENTS)),
):
    existing = db.scalar(select(Student).where(Student.admission_number == payload.admission_number))
    if existing:
        raise HTTPException(status_code=400, detail=f"Admission number '{payload.admission_number}' already exists")

    student = Student(**payload.model_dump(), created_by=current_user.id)
    db.add(student)
    db.flush()
    log_action(db, current_user, "CREATE_STUDENT", "student", student.id,
               None, {"admission_number": payload.admission_number}, request=request)
    db.commit()
    return _enrich(student, db)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_STUDENTS)),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _enrich(student, db)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_STUDENTS)),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    old = {"student_name": student.student_name, "student_status": str(student.student_status)}
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(student, field, value)

    log_action(db, current_user, "UPDATE_STUDENT", "student", student_id, old,
               payload.model_dump(exclude_none=True), request=request)
    db.commit()
    return _enrich(student, db)


@router.delete("/{student_id}", status_code=204)
def delete_student(
    student_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_STUDENTS)),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.student_status = "CANCELLED"
    log_action(db, current_user, "CANCEL_STUDENT", "student", student_id, request=request)
    db.commit()


@router.get("/{student_id}/fee-summary")
def student_fee_summary(
    student_id: int,
    fy_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.VIEW_STUDENTS)),
):
    from app.services.report_service import student_ledger
    return student_ledger(db, student_id, fy_id)


@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.MANAGE_STUDENTS)),
):
    """Bulk import students from Excel. Returns count of imported/failed."""
    import openpyxl

    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot open Excel file: {e}")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="Empty spreadsheet")

    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    imported = 0
    failed = []

    for r_idx, row in enumerate(rows[1:], start=2):
        raw = dict(zip(headers, row))
        adm_no = str(raw.get("admission_number", "") or "").strip()
        student_name = str(raw.get("student_name", "") or "").strip()

        if not adm_no or not student_name:
            failed.append({"row": r_idx, "error": "admission_number and student_name required"})
            continue

        existing = db.scalar(select(Student).where(Student.admission_number == adm_no))
        if existing:
            failed.append({"row": r_idx, "error": f"Duplicate admission_number '{adm_no}'"})
            continue

        try:
            student = Student(
                admission_number=adm_no,
                student_name=student_name,
                father_name=str(raw.get("father_name", "") or "").strip() or None,
                mobile=str(raw.get("mobile", "") or "").strip() or None,
                email=str(raw.get("email", "") or "").strip() or None,
                created_by=current_user.id,
            )
            db.add(student)
            db.flush()
            imported += 1
        except Exception as e:
            failed.append({"row": r_idx, "error": str(e)[:200]})

    db.commit()
    return {"imported": imported, "failed_count": len(failed), "failed_rows": failed[:50]}
