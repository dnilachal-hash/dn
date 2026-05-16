from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from ..database import get_db
from ..models.salary import SalaryStructure, CustomAllowance, EmployeeTaxDeclaration
from ..models.user import User
from ..schemas.salary import (
    SalaryStructureCreate, SalaryStructureOut, TaxDeclarationIn, TaxDeclarationOut
)
from ..core.permissions import require_permission, Permission
from ..services.audit_service import log_action

router = APIRouter(prefix="/salary-structures", tags=["salary"])


def _calc_gross(s: SalaryStructure) -> Decimal:
    total = sum([Decimal(s.basic or 0), Decimal(s.da or 0), Decimal(s.hra or 0),
                 Decimal(s.medical_allowance or 0), Decimal(s.conveyance_allowance or 0),
                 Decimal(s.transport_allowance or 0), Decimal(s.special_allowance or 0),
                 Decimal(s.other_allowance or 0),
                 Decimal(s.children_education_allowance or 0),
                 Decimal(s.uniform_allowance or 0),
                 Decimal(s.telephone_allowance or 0),
                 Decimal(s.internet_allowance or 0),
                 Decimal(s.research_allowance or 0)],
                start=Decimal(0))
    for ca in s.custom_allowances:
        total += Decimal(ca.amount or 0)
    return total


@router.get("", response_model=list[SalaryStructureOut])
def list_structures(employee_id: int | None = None, db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.SALARY_VIEW))):
    q = select(SalaryStructure).options(selectinload(SalaryStructure.custom_allowances))
    if employee_id:
        q = q.where(SalaryStructure.employee_id == employee_id)
    return db.scalars(q.order_by(SalaryStructure.effective_from.desc())).all()


@router.post("", response_model=SalaryStructureOut, status_code=201)
def create_structure(payload: SalaryStructureCreate, db: Session = Depends(get_db),
                     current_user: User = Depends(require_permission(Permission.SALARY_CREATE))):
    data = payload.model_dump(exclude={"custom_allowances"})
    s = SalaryStructure(**data, created_by=current_user.id, status="DRAFT")
    for ca in payload.custom_allowances:
        s.custom_allowances.append(CustomAllowance(**ca.model_dump()))
    s.gross_monthly = _calc_gross(s)
    db.add(s); db.flush()
    log_action(db, current_user, "SALARY_CREATE", "SalaryStructure", s.id, None,
               {"employee_id": s.employee_id, "gross": str(s.gross_monthly)})
    db.commit(); db.refresh(s)
    return s


@router.post("/{structure_id}/activate")
def activate_structure(structure_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(require_permission(Permission.SALARY_CREATE))):
    s = db.get(SalaryStructure, structure_id)
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    # Expire current active
    current = db.scalars(select(SalaryStructure).where(
        SalaryStructure.employee_id == s.employee_id,
        SalaryStructure.status == "ACTIVE",
        SalaryStructure.id != s.id)).all()
    for c in current:
        c.status = "EXPIRED"
        c.effective_to = s.effective_from
    s.status = "ACTIVE"
    s.approved_by = current_user.id
    s.approved_at = datetime.utcnow()
    log_action(db, current_user, "SALARY_ACTIVATE", "SalaryStructure", s.id)
    db.commit()
    return {"ok": True, "id": s.id}


# Tax declarations
tax_router = APIRouter(prefix="/tds", tags=["tds"])


@tax_router.get("/declarations/{employee_id}", response_model=TaxDeclarationOut | None)
def get_declaration(employee_id: int, fy_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(require_permission(Permission.SALARY_VIEW))):
    return db.scalar(select(EmployeeTaxDeclaration).where(
        EmployeeTaxDeclaration.employee_id == employee_id,
        EmployeeTaxDeclaration.financial_year_id == fy_id))


@tax_router.post("/declarations", response_model=TaxDeclarationOut, status_code=201)
def submit_declaration(payload: TaxDeclarationIn, db: Session = Depends(get_db),
                       current_user: User = Depends(require_permission(Permission.SALARY_CREATE))):
    existing = db.scalar(select(EmployeeTaxDeclaration).where(
        EmployeeTaxDeclaration.employee_id == payload.employee_id,
        EmployeeTaxDeclaration.financial_year_id == payload.financial_year_id))
    if existing:
        for k, v in payload.model_dump().items():
            setattr(existing, k, v)
        existing.declaration_submitted_at = datetime.utcnow()
        log_action(db, current_user, "TAX_DECL_UPDATE", "TaxDeclaration", existing.id)
        db.commit(); db.refresh(existing)
        return existing
    decl = EmployeeTaxDeclaration(**payload.model_dump(),
                                   declaration_submitted_at=datetime.utcnow())
    db.add(decl); db.flush()
    log_action(db, current_user, "TAX_DECL_CREATE", "TaxDeclaration", decl.id)
    db.commit(); db.refresh(decl)
    return decl


@tax_router.post("/calculate/{employee_id}")
def calculate_tds_endpoint(employee_id: int, month: int, year: int,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(require_permission(Permission.PAYROLL_VIEW))):
    from ..services.tds_service import calculate_tds
    return calculate_tds(db, employee_id, month, year)
