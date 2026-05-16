from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..database import get_db
from ..models.employee import Department, Designation, Employee
from ..models.user import User
from ..schemas.employee import DepartmentCreate, DepartmentOut, DesignationCreate, DesignationOut
from ..core.permissions import require_permission, Permission, require_role
from ..services.audit_service import log_action

router = APIRouter(tags=["departments"])


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db),
                     current_user: User = Depends(require_permission(Permission.EMPLOYEE_VIEW))):
    return db.scalars(select(Department).order_by(Department.type, Department.name)).all()


@router.post("/departments", response_model=DepartmentOut, status_code=201)
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(require_role("super_admin", "admin", "hr_manager"))):
    if db.scalar(select(Department).where(Department.name == payload.name)):
        raise HTTPException(status_code=409, detail="Department exists")
    d = Department(**payload.model_dump())
    db.add(d); db.flush()
    log_action(db, current_user, "DEPT_CREATE", "Department", d.id, None, payload.model_dump())
    db.commit(); db.refresh(d)
    return d


@router.put("/departments/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: int, payload: DepartmentCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(require_role("super_admin", "admin"))):
    d = db.get(Department, dept_id)
    if not d:
        raise HTTPException(status_code=404, detail="Not found")
    old = {"name": d.name, "is_active": d.is_active}
    for k, v in payload.model_dump().items():
        setattr(d, k, v)
    log_action(db, current_user, "DEPT_UPDATE", "Department", d.id, old, payload.model_dump())
    db.commit(); db.refresh(d)
    return d


@router.get("/designations", response_model=list[DesignationOut])
def list_designations(department_id: int | None = None, db: Session = Depends(get_db),
                      current_user: User = Depends(require_permission(Permission.EMPLOYEE_VIEW))):
    q = select(Designation)
    if department_id:
        q = q.where(Designation.department_id == department_id)
    return db.scalars(q.order_by(Designation.name)).all()


@router.post("/designations", response_model=DesignationOut, status_code=201)
def create_designation(payload: DesignationCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(require_role("super_admin", "admin", "hr_manager"))):
    d = Designation(**payload.model_dump())
    db.add(d); db.flush()
    log_action(db, current_user, "DESIG_CREATE", "Designation", d.id)
    db.commit(); db.refresh(d)
    return d
