from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, and_
from io import BytesIO

from ..database import get_db
from ..models.employee import Employee, EmployeeBankDetail, Department, Designation
from ..models.user import User
from ..schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut, DepartmentCreate, DepartmentOut,
    DesignationCreate, DesignationOut, BankDetailOut
)
from ..core.permissions import require_permission, Permission, has_permission
from ..core.security import encrypt, decrypt, mask_pan, mask_aadhaar, mask_account
from ..services.audit_service import log_action
from ..services import import_service

router = APIRouter(prefix="/employees", tags=["employees"])


def _to_out(emp: Employee, show_sensitive: bool = False) -> dict:
    data = {
        "id": emp.id, "emp_code": emp.emp_code,
        "first_name": emp.first_name, "last_name": emp.last_name,
        "email": emp.email, "phone": emp.phone,
        "dob": emp.dob, "gender": emp.gender,
        "marital_status": emp.marital_status,
        "father_name": emp.father_name, "mother_name": emp.mother_name,
        "spouse_name": emp.spouse_name,
        "address": emp.address, "state": emp.state,
        "uan": emp.uan, "esi_ip_number": emp.esi_ip_number,
        "department_id": emp.department_id, "designation_id": emp.designation_id,
        "date_of_joining": emp.date_of_joining, "date_of_exit": emp.date_of_exit,
        "employment_type": emp.employment_type, "is_active": emp.is_active,
        "epf_applicable": emp.epf_applicable, "esi_applicable": emp.esi_applicable,
        "pt_applicable": emp.pt_applicable, "lwf_applicable": emp.lwf_applicable,
        "tds_applicable": emp.tds_applicable,
        "city_tier": emp.city_tier, "state_for_pt": emp.state_for_pt,
        "created_at": emp.created_at,
        "bank_details": [
            {"id": b.id,
             "account_masked": mask_account(decrypt(b.account_number_encrypted)) if not show_sensitive
                                else decrypt(b.account_number_encrypted),
             "ifsc": b.ifsc, "bank_name": b.bank_name, "branch": b.branch,
             "is_primary": b.is_primary}
            for b in emp.bank_details
        ],
    }
    if show_sensitive:
        data["pan_masked"] = decrypt(emp.pan_encrypted)
        data["aadhaar_masked"] = decrypt(emp.aadhaar_encrypted)
    else:
        data["pan_masked"] = mask_pan(decrypt(emp.pan_encrypted))
        data["aadhaar_masked"] = mask_aadhaar(decrypt(emp.aadhaar_encrypted))
    return data


@router.get("")
def list_employees(department_id: int | None = None, is_active: bool | None = None,
                   search: str | None = None, page: int = 1, page_size: int = 50,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(require_permission(Permission.EMPLOYEE_VIEW))):
    q = select(Employee).options(selectinload(Employee.bank_details))
    if department_id:
        q = q.where(Employee.department_id == department_id)
    if is_active is not None:
        q = q.where(Employee.is_active == is_active)
    if search:
        like = f"%{search}%"
        q = q.where(Employee.first_name.ilike(like) | Employee.emp_code.ilike(like)
                    | Employee.last_name.ilike(like))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.offset((page - 1) * page_size).limit(page_size)).all()
    show_sens = has_permission(current_user.role, Permission.EMPLOYEE_VIEW_SENSITIVE)
    return {
        "items": [_to_out(e, show_sens) for e in rows],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db),
                 current_user: User = Depends(require_permission(Permission.EMPLOYEE_VIEW))):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Not found")
    show_sens = has_permission(current_user.role, Permission.EMPLOYEE_VIEW_SENSITIVE)
    return _to_out(emp, show_sens)


@router.post("", status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.EMPLOYEE_CREATE))):
    if db.scalar(select(Employee).where(Employee.emp_code == payload.emp_code)):
        raise HTTPException(status_code=409, detail="Employee code already exists")
    emp = Employee(**payload.model_dump(exclude={"pan", "aadhaar", "uan", "esi_ip_number",
                                                  "bank_details"}))
    emp.pan_encrypted = encrypt(payload.pan)
    emp.aadhaar_encrypted = encrypt(payload.aadhaar)
    emp.uan = payload.uan
    emp.esi_ip_number = payload.esi_ip_number
    for b in (payload.bank_details or []):
        emp.bank_details.append(EmployeeBankDetail(
            account_number_encrypted=encrypt(b.account_number),
            ifsc=b.ifsc, bank_name=b.bank_name, branch=b.branch, is_primary=b.is_primary))
    db.add(emp); db.flush()
    log_action(db, current_user, "EMPLOYEE_CREATE", "Employee", emp.id, None,
               {"emp_code": emp.emp_code})
    db.commit(); db.refresh(emp)
    return _to_out(emp, True)


@router.put("/{employee_id}")
def update_employee(employee_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.EMPLOYEE_EDIT))):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    old = {k: getattr(emp, k) for k in data if hasattr(emp, k)}
    pan = data.pop("pan", None)
    aadhaar = data.pop("aadhaar", None)
    for k, v in data.items():
        setattr(emp, k, v)
    if pan:
        emp.pan_encrypted = encrypt(pan)
    if aadhaar:
        emp.aadhaar_encrypted = encrypt(aadhaar)
    log_action(db, current_user, "EMPLOYEE_UPDATE", "Employee", emp.id, old, data)
    db.commit(); db.refresh(emp)
    return _to_out(emp, has_permission(current_user.role, Permission.EMPLOYEE_VIEW_SENSITIVE))


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.EMPLOYEE_DELETE))):
    emp = db.get(Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Not found")
    emp.is_active = False
    log_action(db, current_user, "EMPLOYEE_DEACTIVATE", "Employee", emp.id)
    db.commit()
    return Response(status_code=204)


@router.get("/import/template")
def employee_template():
    data = import_service.template_employees()
    return StreamingResponse(BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=employees_template.xlsx"})


@router.post("/import")
def bulk_import(file: UploadFile = File(...), db: Session = Depends(get_db),
                current_user: User = Depends(require_permission(Permission.IMPORT_BULK))):
    content = file.file.read()
    result = import_service.import_employees(db, content)
    log_action(db, current_user, "EMPLOYEE_BULK_IMPORT", "Employee", None, None,
               {"inserted": result["inserted"], "errors_count": len(result["errors"])})
    db.commit()
    return result
