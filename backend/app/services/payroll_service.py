"""Payroll Generation Engine — full 20-step computation pipeline."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import calendar
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from ..models.employee import Employee
from ..models.salary import SalaryStructure, CustomAllowance
from ..models.payroll import (
    PayrollMonth, PayrollRecord, PayrollCustomComponent, PayrollStatus, PaymentStatus
)
from ..models.statutory import EPFSetting, ESISetting, PTStateSetting, LWFSetting
from ..models.attendance import AttendanceRecord
from ..models.loan import EmployeeLoan, LoanTransaction
from ..models.compliance import ComplianceAlert
from ..models.tds import TDSCalculation
from ..core.exceptions import ComplianceBlockError, PayrollLockedError
from .tds_service import calculate_tds

ZERO = Decimal("0.00")


def q(x) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def working_days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _proration_factor(paid_days: Decimal, working_days: int) -> Decimal:
    if working_days <= 0:
        return Decimal(0)
    return Decimal(paid_days) / Decimal(working_days)


def _get_active_structure(db: Session, employee_id: int, on_date: date) -> SalaryStructure | None:
    return db.scalar(
        select(SalaryStructure).where(
            and_(
                SalaryStructure.employee_id == employee_id,
                SalaryStructure.status == "ACTIVE",
                SalaryStructure.effective_from <= on_date,
                (SalaryStructure.effective_to.is_(None)) | (SalaryStructure.effective_to >= on_date),
            )
        ).order_by(SalaryStructure.effective_from.desc())
    )


def _pt_amount(db: Session, state_code: str | None, fy_id: int, gross: Decimal,
               month: int) -> Decimal:
    if not state_code:
        return Decimal(0)
    pt = db.scalar(select(PTStateSetting).where(
        and_(PTStateSetting.state_code == state_code,
             PTStateSetting.financial_year_id == fy_id)))
    if not pt or not pt.slabs:
        return Decimal(0)
    for slab in pt.slabs:
        mn = Decimal(str(slab.get("min") or 0))
        mx = slab.get("max")
        amt = Decimal(str(slab.get("amount") or 0))
        if mx is None or gross <= Decimal(str(mx)):
            if gross >= mn:
                return amt
    return Decimal(0)


def _lwf_amount(db: Session, state_code: str | None, fy_id: int, month: int) -> tuple[Decimal, Decimal]:
    if not state_code:
        return Decimal(0), Decimal(0)
    lwf = db.scalar(select(LWFSetting).where(
        and_(LWFSetting.state_code == state_code,
             LWFSetting.financial_year_id == fy_id)))
    if not lwf:
        return Decimal(0), Decimal(0)
    if lwf.periodicity == "MONTHLY":
        return Decimal(lwf.employee_amount), Decimal(lwf.employer_amount)
    if lwf.periodicity == "SEMI_ANNUAL" and month in (3, 9):
        return Decimal(lwf.employee_amount), Decimal(lwf.employer_amount)
    if lwf.periodicity == "ANNUAL" and month == 3:
        return Decimal(lwf.employee_amount), Decimal(lwf.employer_amount)
    return Decimal(0), Decimal(0)


def _loan_emi(db: Session, employee_id: int, month: int, year: int) -> Decimal:
    loans = db.scalars(select(EmployeeLoan).where(
        and_(EmployeeLoan.employee_id == employee_id,
             EmployeeLoan.status == "ACTIVE"))).all()
    total = Decimal(0)
    for ln in loans:
        if ln.paid_installments >= ln.total_installments:
            continue
        # only if month >= start month
        loan_start = (ln.start_year, ln.start_month)
        if (year, month) >= loan_start:
            emi = min(Decimal(ln.emi_amount), Decimal(ln.outstanding_balance))
            total += emi
    return total


def _attendance(db: Session, employee_id: int, month: int, year: int,
                default_working: int) -> tuple[int, Decimal, Decimal, Decimal]:
    a = db.scalar(select(AttendanceRecord).where(
        and_(AttendanceRecord.employee_id == employee_id,
             AttendanceRecord.month == month,
             AttendanceRecord.year == year)))
    if a:
        wd = int(a.working_days)
        return wd, a.present_days, a.lop_days, a.overtime_hours
    return default_working, Decimal(default_working), Decimal(0), Decimal(0)


def calculate_payroll_for_employee(db: Session, employee: Employee, pm: PayrollMonth,
                                   alerts: list, override_working_days: int | None = None) -> PayrollRecord | None:
    """Compute payroll for a single employee. Returns record (uncommitted) or None if blocking alert raised."""
    on_date = date(pm.year, pm.month, 1)
    structure = _get_active_structure(db, employee.id, on_date)
    if not structure:
        alerts.append(ComplianceAlert(
            employee_id=employee.id, payroll_month_id=pm.id,
            alert_type="NO_SALARY_STRUCTURE", severity="CRITICAL",
            message=f"No active salary structure for employee {employee.emp_code} on {on_date}"
        ))
        return None

    # Exit check
    if employee.date_of_exit and employee.date_of_exit < on_date:
        alerts.append(ComplianceAlert(
            employee_id=employee.id, payroll_month_id=pm.id,
            alert_type="EXIT_BEFORE_MONTH", severity="CRITICAL",
            message=f"Employee {employee.emp_code} exited before payroll month"
        ))
        return None

    is_new_joiner = bool(employee.date_of_joining and
                          employee.date_of_joining.year == pm.year and
                          employee.date_of_joining.month == pm.month)
    is_exit_month = bool(employee.date_of_exit and
                          employee.date_of_exit.year == pm.year and
                          employee.date_of_exit.month == pm.month)

    fy_id = pm.financial_year_id
    epf = db.scalar(select(EPFSetting).where(EPFSetting.financial_year_id == fy_id))
    esi = db.scalar(select(ESISetting).where(ESISetting.financial_year_id == fy_id))

    working_days = override_working_days or pm.working_days or working_days_in_month(pm.year, pm.month)
    wd, present, lop, ot_hours = _attendance(db, employee.id, pm.month, pm.year, working_days)

    paid_days = max(present - Decimal(0), Decimal(0))
    factor = _proration_factor(paid_days, wd)

    # ---- Earnings (pro-rated) ----
    basic = q(Decimal(structure.basic) * factor)
    da = q(Decimal(structure.da) * factor)
    hra = q(Decimal(structure.hra) * factor)
    med = q(Decimal(structure.medical_allowance) * factor)
    conv = q(Decimal(structure.conveyance_allowance) * factor)
    trans = q(Decimal(structure.transport_allowance) * factor)
    spec = q(Decimal(structure.special_allowance) * factor)
    other = q(Decimal(structure.other_allowance) * factor)
    cea = q(Decimal(structure.children_education_allowance) * factor)
    uni = q(Decimal(structure.uniform_allowance) * factor)
    tel = q(Decimal(structure.telephone_allowance) * factor)
    inet = q(Decimal(structure.internet_allowance) * factor)
    research = q(Decimal(structure.research_allowance) * factor)

    custom_total = Decimal(0)
    custom_pf_eligible = Decimal(0)
    custom_components_payload = []
    for ca in structure.custom_allowances:
        amt = q(Decimal(ca.amount) * factor)
        custom_total += amt
        if ca.is_pf_eligible:
            custom_pf_eligible += amt
        custom_components_payload.append({
            "name": ca.name, "amount": amt, "type": "EARNING", "is_taxable": ca.is_taxable
        })

    gross = (basic + da + hra + med + conv + trans + spec + other + cea + uni + tel + inet + research + custom_total)
    gross = q(gross)

    # ---- PF Wage ----
    if structure.pf_wage_override:
        pf_wage = q(Decimal(structure.pf_wage_override) * factor)
    else:
        pf_wage_base = basic + da + custom_pf_eligible
        if epf and epf.pf_wage_ceiling and Decimal(epf.pf_wage_ceiling) > 0 and not employee.epf_applicable:
            pf_wage = Decimal(0)
        else:
            pf_wage = pf_wage_base

    # ---- EPF ----
    if employee.epf_applicable and epf:
        epf_employee = q(pf_wage * Decimal(epf.employee_rate) / Decimal(100))
        epf_employer_full = q(pf_wage * Decimal(epf.employer_rate) / Decimal(100))
        eps_base = min(pf_wage, Decimal(epf.eps_wage_ceiling or 0))
        eps = q(eps_base * Decimal(epf.eps_rate) / Decimal(100))
        epf_to_trust = q(epf_employer_full - eps)
        epf_employer = epf_to_trust  # employer's PF share (after EPS deduction)
        edli_base = min(pf_wage, Decimal(epf.edli_wage_ceiling or 0))
        edli = q(edli_base * Decimal(epf.edli_rate) / Decimal(100))
        epf_admin = q(pf_wage * Decimal(epf.admin_charge_rate) / Decimal(100))
    else:
        epf_employee = epf_employer = eps = edli = epf_admin = Decimal(0)

    # ---- ESI ----
    esi_employee = esi_employer = Decimal(0)
    esi_wage = Decimal(0)
    if employee.esi_applicable and esi:
        ceiling = Decimal(esi.wage_ceiling or 0)
        if gross <= ceiling:
            esi_wage = gross
            esi_employee = q(esi_wage * Decimal(esi.employee_rate) / Decimal(100))
            esi_employer = q(esi_wage * Decimal(esi.employer_rate) / Decimal(100))

    # ---- PT ----
    pt = _pt_amount(db, employee.state_for_pt, fy_id, gross, pm.month) if employee.pt_applicable else Decimal(0)

    # ---- LWF ----
    lwf_emp, lwf_employer = _lwf_amount(db, employee.state_for_pt, fy_id, pm.month) if employee.lwf_applicable else (Decimal(0), Decimal(0))

    # ---- Loan EMI ----
    loan = _loan_emi(db, employee.id, pm.month, pm.year)

    # ---- TDS ----
    tds_result = calculate_tds(db, employee.id, pm.month, pm.year)
    tds_amt = tds_result.get("monthly_tds", Decimal(0))

    # ---- Totals ----
    total_deductions = q(epf_employee + esi_employee + tds_amt + pt + lwf_emp + loan)
    net_salary = q(gross - total_deductions)

    if net_salary < Decimal(0):
        alerts.append(ComplianceAlert(
            employee_id=employee.id, payroll_month_id=pm.id,
            alert_type="NEGATIVE_NET", severity="CRITICAL",
            message=f"Net salary negative for {employee.emp_code}: {net_salary}"
        ))
        return None

    if gross > 0 and (total_deductions / gross) > Decimal("0.5"):
        alerts.append(ComplianceAlert(
            employee_id=employee.id, payroll_month_id=pm.id,
            alert_type="EXCESS_DEDUCTION", severity="WARNING",
            message=f"Deductions exceed 50% of gross for {employee.emp_code}"
        ))

    # ---- Employer side ----
    gratuity_provision = q(basic * Decimal("4.81") / Decimal(100))  # standard 4.81%
    bonus_provision = q(min(basic, Decimal("7000")) * Decimal("8.33") / Decimal(100))
    employer_total = q(epf_employer + eps + edli + epf_admin + esi_employer + lwf_employer + gratuity_provision + bonus_provision)
    ctc = q(gross + employer_total)

    record = PayrollRecord(
        payroll_month_id=pm.id,
        employee_id=employee.id,
        salary_structure_id=structure.id,
        working_days=wd, paid_days=paid_days, lop_days=lop,
        is_new_joiner=is_new_joiner, is_exit_month=is_exit_month,
        basic=basic, da=da, hra=hra,
        medical_allowance=med, conveyance_allowance=conv, transport_allowance=trans,
        special_allowance=spec, other_allowance=other,
        children_education_allowance=cea, uniform_allowance=uni,
        telephone_allowance=tel, internet_allowance=inet, research_allowance=research,
        overtime_pay=Decimal(0), bonus=Decimal(0), arrears=Decimal(0), reimbursement=Decimal(0),
        gross_salary=gross,
        pf_wage=pf_wage, epf_employee=epf_employee,
        esi_wage=esi_wage, esi_employee=esi_employee,
        tds=tds_amt, professional_tax=pt, lwf_employee=lwf_emp,
        loan_emi=loan, advance_recovery=Decimal(0), other_deductions=Decimal(0),
        total_deductions=total_deductions, net_salary=net_salary,
        epf_employer=epf_employer, eps=eps, edli=edli, epf_admin=epf_admin,
        esi_employer=esi_employer, lwf_employer=lwf_employer,
        gratuity_provision=gratuity_provision, bonus_provision=bonus_provision,
        employer_total=employer_total, ctc=ctc,
        status=PayrollStatus.GENERATED.value,
        payment_status=PaymentStatus.PENDING.value,
        data_source="LIVE",
    )

    for cc in custom_components_payload:
        record.custom_components.append(PayrollCustomComponent(**cc))

    # Persist TDS calculation record
    if not tds_result.get("skipped"):
        tds_calc = TDSCalculation(
            employee_id=employee.id,
            financial_year_id=fy_id,
            month=pm.month, year=pm.year,
            projected_annual_gross=tds_result["projected_annual_gross"],
            hra_exemption=tds_result["hra_exemption"],
            standard_deduction=tds_result["standard_deduction"],
            chapter_via_deduction=tds_result["chapter_via_deduction"],
            taxable_income=tds_result["taxable_income"],
            tax_old_regime=tds_result["tax_old_regime"],
            tax_new_regime=tds_result["tax_new_regime"],
            tax_regime_applied=tds_result["tax_regime_applied"],
            surcharge=tds_result["surcharge"],
            cess=tds_result["cess"],
            rebate=tds_result["rebate"],
            annual_tax=tds_result["annual_tax"],
            tds_to_date=tds_result["tds_to_date"],
            remaining_months=tds_result["remaining_months"],
            monthly_tds=tds_amt,
        )
        db.add(tds_calc)

    return record


def generate_payroll_month(db: Session, pm: PayrollMonth, user_id: int,
                           employee_ids: list[int] | None = None,
                           department_id: int | None = None) -> dict:
    """Generate payroll records for all (or selected) employees of the month."""
    if pm.status == PayrollStatus.LOCKED.value:
        raise PayrollLockedError()

    q_emp = select(Employee).where(Employee.is_active == True)
    if employee_ids:
        q_emp = q_emp.where(Employee.id.in_(employee_ids))
    if department_id:
        q_emp = q_emp.where(Employee.department_id == department_id)
    employees = db.scalars(q_emp).all()

    # Wipe existing draft records for these employees in this month
    existing = db.scalars(select(PayrollRecord).where(
        and_(PayrollRecord.payroll_month_id == pm.id,
             PayrollRecord.employee_id.in_([e.id for e in employees])))).all()
    for r in existing:
        if r.status == PayrollStatus.LOCKED.value or r.status == PayrollStatus.PAID.value:
            continue
        db.delete(r)
    db.flush()

    alerts: list = []
    generated = 0
    skipped = 0
    for emp in employees:
        try:
            rec = calculate_payroll_for_employee(db, emp, pm, alerts)
            if rec is None:
                skipped += 1
                continue
            db.add(rec)
            generated += 1
        except Exception as e:
            alerts.append(ComplianceAlert(
                employee_id=emp.id, payroll_month_id=pm.id,
                alert_type="CALC_ERROR", severity="CRITICAL",
                message=f"Error: {e}"
            ))
            skipped += 1

    for a in alerts:
        db.add(a)

    from datetime import datetime
    pm.status = PayrollStatus.GENERATED.value
    pm.generated_at = datetime.utcnow()
    pm.generated_by = user_id

    db.flush()
    return {"generated": generated, "skipped": skipped,
            "alerts": len(alerts),
            "critical": sum(1 for a in alerts if a.severity == "CRITICAL")}
