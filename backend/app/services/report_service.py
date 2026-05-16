"""Report data assembly — produces row data for PDF/Excel renderers."""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from ..models.payroll import PayrollMonth, PayrollRecord
from ..models.employee import Employee, Department
from ..models.org import Organisation, FinancialYear

MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def get_org(db: Session) -> Organisation | None:
    return db.scalar(select(Organisation).order_by(Organisation.id).limit(1))


def monthly_payroll_summary(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    rows = db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == payroll_month_id
    )).all()
    columns = ["Emp Code", "Name", "Department", "Designation",
               "Gross", "EPF", "ESI", "TDS", "PT", "Net", "CTC"]
    data_rows = []
    totals = [Decimal(0)] * 7  # gross, epf, esi, tds, pt, net, ctc
    for r in rows:
        emp = r.employee
        dept = emp.department.name if emp.department else "-"
        desig = emp.designation.name if emp.designation else "-"
        data_rows.append([
            emp.emp_code,
            f"{emp.first_name} {emp.last_name or ''}".strip(),
            dept, desig,
            float(r.gross_salary), float(r.epf_employee), float(r.esi_employee),
            float(r.tds), float(r.professional_tax), float(r.net_salary), float(r.ctc),
        ])
        totals[0] += Decimal(r.gross_salary)
        totals[1] += Decimal(r.epf_employee)
        totals[2] += Decimal(r.esi_employee)
        totals[3] += Decimal(r.tds)
        totals[4] += Decimal(r.professional_tax)
        totals[5] += Decimal(r.net_salary)
        totals[6] += Decimal(r.ctc)
    data_rows.append([
        "TOTAL", "", "", "",
        float(totals[0]), float(totals[1]), float(totals[2]),
        float(totals[3]), float(totals[4]), float(totals[5]), float(totals[6])
    ])
    title = f"Monthly Payroll Summary — {MONTHS[pm.month]} {pm.year}"
    summary = {
        "Month": f"{MONTHS[pm.month]} {pm.year}",
        "Status": pm.status,
        "Total Employees": len(rows),
        "Working Days": pm.working_days,
    }
    return title, columns, data_rows, summary


def department_cost_report(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    rows = db.execute(
        select(
            Department.name, Department.type,
            func.count(PayrollRecord.id).label("headcount"),
            func.sum(PayrollRecord.gross_salary).label("gross"),
            func.sum(PayrollRecord.net_salary).label("net"),
            func.sum(PayrollRecord.employer_total).label("employer"),
            func.sum(PayrollRecord.ctc).label("ctc"),
        )
        .join(Employee, Employee.department_id == Department.id)
        .join(PayrollRecord, PayrollRecord.employee_id == Employee.id)
        .where(PayrollRecord.payroll_month_id == payroll_month_id)
        .group_by(Department.id)
    ).all()
    data = []
    for r in rows:
        data.append([r.name, r.type, r.headcount,
                     float(r.gross or 0), float(r.net or 0),
                     float(r.employer or 0), float(r.ctc or 0)])
    columns = ["Department", "Type", "Headcount", "Gross", "Net",
               "Employer Liability", "CTC"]
    return (f"Department-wise Cost — {MONTHS[pm.month]} {pm.year}",
            columns, data, None)


def bank_transfer_report(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    from ..core.security import decrypt
    rows = db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == payroll_month_id)).all()
    data = []
    for r in rows:
        emp = r.employee
        bank = emp.bank_details[0] if emp.bank_details else None
        if not bank:
            continue
        acc = decrypt(bank.account_number_encrypted) or ""
        data.append([emp.emp_code,
                     f"{emp.first_name} {emp.last_name or ''}".strip(),
                     bank.bank_name, bank.ifsc, acc, float(r.net_salary)])
    return ("Bank Transfer File — " + f"{MONTHS[pm.month]} {pm.year}",
            ["Emp Code", "Name", "Bank", "IFSC", "Account No.", "Amount"],
            data, {"Total Records": len(data)})


def epf_ecr_report(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    rows = db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == payroll_month_id,
        PayrollRecord.epf_employee > 0
    )).all()
    data = []
    for r in rows:
        emp = r.employee
        data.append([emp.uan or "", emp.emp_code,
                     f"{emp.first_name} {emp.last_name or ''}".strip(),
                     float(r.pf_wage), float(r.epf_employee),
                     float(r.epf_employer), float(r.eps), float(r.edli)])
    return ("EPF Monthly Return (ECR) — " + f"{MONTHS[pm.month]} {pm.year}",
            ["UAN", "Emp Code", "Name", "PF Wage", "EE Share", "ER Share", "EPS", "EDLI"],
            data, None)


def esi_report(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    rows = db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == payroll_month_id,
        PayrollRecord.esi_employee > 0)).all()
    data = []
    for r in rows:
        emp = r.employee
        data.append([emp.esi_ip_number or "", emp.emp_code,
                     f"{emp.first_name} {emp.last_name or ''}".strip(),
                     float(r.esi_wage), float(r.esi_employee), float(r.esi_employer)])
    return (f"ESI Monthly — {MONTHS[pm.month]} {pm.year}",
            ["IP Number", "Emp Code", "Name", "ESI Wage", "EE", "ER"], data, None)


def tds_monthly_report(db: Session, payroll_month_id: int):
    pm = db.get(PayrollMonth, payroll_month_id)
    if not pm:
        return None
    from ..core.security import decrypt, mask_pan
    rows = db.scalars(select(PayrollRecord).where(
        PayrollRecord.payroll_month_id == payroll_month_id,
        PayrollRecord.tds > 0)).all()
    data = []
    for r in rows:
        emp = r.employee
        data.append([emp.emp_code,
                     f"{emp.first_name} {emp.last_name or ''}".strip(),
                     mask_pan(decrypt(emp.pan_encrypted)) or "",
                     float(r.gross_salary), float(r.tds)])
    return (f"TDS Monthly — {MONTHS[pm.month]} {pm.year}",
            ["Emp Code", "Name", "PAN", "Gross", "TDS Deducted"], data, None)


def employee_annual_statement(db: Session, employee_id: int, fy_id: int):
    fy = db.get(FinancialYear, fy_id)
    emp = db.get(Employee, employee_id)
    if not fy or not emp:
        return None
    rows = db.execute(
        select(PayrollRecord, PayrollMonth)
        .join(PayrollMonth, PayrollMonth.id == PayrollRecord.payroll_month_id)
        .where(and_(PayrollRecord.employee_id == employee_id,
                    PayrollMonth.financial_year_id == fy_id))
        .order_by(PayrollMonth.year, PayrollMonth.month)
    ).all()
    data = []
    totals = {"gross": Decimal(0), "epf": Decimal(0), "tds": Decimal(0),
              "net": Decimal(0)}
    for r, pm in rows:
        data.append([f"{MONTHS[pm.month]} {pm.year}",
                     float(r.gross_salary), float(r.epf_employee),
                     float(r.esi_employee), float(r.tds),
                     float(r.professional_tax), float(r.net_salary)])
        totals["gross"] += Decimal(r.gross_salary)
        totals["epf"] += Decimal(r.epf_employee)
        totals["tds"] += Decimal(r.tds)
        totals["net"] += Decimal(r.net_salary)
    data.append(["TOTAL", float(totals["gross"]), float(totals["epf"]),
                 "", float(totals["tds"]), "", float(totals["net"])])
    return (f"Annual Salary Statement — {emp.emp_code} ({fy.year_label})",
            ["Month", "Gross", "EPF", "ESI", "TDS", "PT", "Net"], data,
            {"Employee": f"{emp.first_name} {emp.last_name or ''}",
             "Department": emp.department.name if emp.department else "-"})
