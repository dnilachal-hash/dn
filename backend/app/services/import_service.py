"""Bulk import via Excel — employees, salaries, attendance, historical payroll."""
from io import BytesIO
from decimal import Decimal
from datetime import date, datetime
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models.employee import Employee, EmployeeBankDetail, Department, Designation
from ..models.salary import SalaryStructure
from ..models.attendance import AttendanceRecord
from ..models.payroll import PayrollRecord, PayrollMonth, PayrollStatus
from ..models.org import FinancialYear
from ..core.security import encrypt


def template_employees() -> bytes:
    wb = Workbook(); ws = wb.active; ws.title = "Employees"
    cols = ["emp_code", "first_name", "last_name", "email", "phone", "dob (YYYY-MM-DD)",
            "gender", "marital_status", "father_name", "address", "state",
            "pan", "aadhaar", "uan", "esi_ip_number",
            "department_name", "designation_name", "date_of_joining (YYYY-MM-DD)",
            "employment_type", "city_tier", "state_for_pt",
            "bank_account", "bank_ifsc", "bank_name", "bank_branch"]
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        ws.column_dimensions[chr(64 + i if i <= 26 else 64 + i // 26)].width = 18
    ws.cell(row=2, column=1, value="EMP001")
    ws.cell(row=2, column=2, value="John")
    ws.cell(row=2, column=3, value="Doe")
    ws.cell(row=2, column=18, value="2024-04-01")
    ws.cell(row=2, column=19, value="PERMANENT")
    buf = BytesIO(); wb.save(buf); return buf.getvalue()


def template_salary_structures() -> bytes:
    wb = Workbook(); ws = wb.active; ws.title = "Salary"
    cols = ["emp_code", "financial_year", "effective_from", "basic", "da", "hra",
            "medical_allowance", "conveyance_allowance", "transport_allowance",
            "special_allowance", "other_allowance", "children_education_allowance",
            "uniform_allowance", "telephone_allowance", "internet_allowance",
            "research_allowance"]
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
    buf = BytesIO(); wb.save(buf); return buf.getvalue()


def template_historical_payroll() -> bytes:
    wb = Workbook(); ws = wb.active; ws.title = "Historical"
    cols = ["emp_code", "month", "year", "basic", "da", "hra", "special_allowance",
            "other_allowance", "gross_salary", "epf_employee", "esi_employee",
            "tds", "professional_tax", "lwf_employee", "total_deductions",
            "net_salary", "epf_employer", "esi_employer", "ctc"]
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=1, column=i, value=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E79")
    buf = BytesIO(); wb.save(buf); return buf.getvalue()


def _parse_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, (date, datetime)):
        return v if isinstance(v, date) and not isinstance(v, datetime) else v.date()
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date()
    except Exception:
        return None


def _dec(v):
    if v is None or v == "":
        return Decimal(0)
    return Decimal(str(v))


def import_employees(db: Session, file_bytes: bytes) -> dict:
    wb = load_workbook(BytesIO(file_bytes))
    ws = wb.active
    header = [c.value for c in ws[1]]
    h = {name: i for i, name in enumerate(header)}
    inserted, errors = 0, []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not row[h["emp_code"]]:
            continue
        emp_code = str(row[h["emp_code"]]).strip()
        existing = db.scalar(select(Employee).where(Employee.emp_code == emp_code))
        if existing:
            errors.append({"row": row_idx, "code": emp_code, "error": "duplicate emp_code"})
            continue
        dept = None
        if row[h["department_name"]]:
            dept = db.scalar(select(Department).where(Department.name == row[h["department_name"]]))
        desig = None
        if row[h["designation_name"]]:
            desig = db.scalar(select(Designation).where(Designation.name == row[h["designation_name"]]))
        emp = Employee(
            emp_code=emp_code,
            first_name=row[h["first_name"]] or "",
            last_name=row[h["last_name"]],
            email=row[h["email"]],
            phone=str(row[h["phone"]]) if row[h["phone"]] else None,
            dob=_parse_date(row[h["dob (YYYY-MM-DD)"]]),
            gender=row[h["gender"]],
            marital_status=row[h["marital_status"]],
            father_name=row[h["father_name"]],
            address=row[h["address"]],
            state=row[h["state"]],
            pan_encrypted=encrypt(row[h["pan"]]) if row[h["pan"]] else None,
            aadhaar_encrypted=encrypt(str(row[h["aadhaar"]])) if row[h["aadhaar"]] else None,
            uan=str(row[h["uan"]]) if row[h["uan"]] else None,
            esi_ip_number=str(row[h["esi_ip_number"]]) if row[h["esi_ip_number"]] else None,
            department_id=dept.id if dept else None,
            designation_id=desig.id if desig else None,
            date_of_joining=_parse_date(row[h["date_of_joining (YYYY-MM-DD)"]]),
            employment_type=row[h["employment_type"]] or "PERMANENT",
            city_tier=row[h["city_tier"]] or "NON_METRO",
            state_for_pt=row[h["state_for_pt"]],
        )
        if row[h["bank_account"]]:
            emp.bank_details.append(EmployeeBankDetail(
                account_number_encrypted=encrypt(str(row[h["bank_account"]])),
                ifsc=row[h["bank_ifsc"]] or "",
                bank_name=row[h["bank_name"]] or "",
                branch=row[h["bank_branch"]],
                is_primary=True,
            ))
        db.add(emp)
        inserted += 1
    db.flush()
    return {"inserted": inserted, "errors": errors}


def import_historical_payroll(db: Session, file_bytes: bytes, fy_id: int) -> dict:
    wb = load_workbook(BytesIO(file_bytes))
    ws = wb.active
    header = [c.value for c in ws[1]]
    h = {name: i for i, name in enumerate(header)}
    inserted, errors = 0, []
    fy = db.get(FinancialYear, fy_id)
    if not fy:
        return {"inserted": 0, "errors": [{"error": "Invalid FY"}]}
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not row[h["emp_code"]]:
            continue
        emp = db.scalar(select(Employee).where(Employee.emp_code == row[h["emp_code"]]))
        if not emp:
            errors.append({"row": row_idx, "error": f"Unknown emp_code: {row[h['emp_code']]}"})
            continue
        month, year = int(row[h["month"]]), int(row[h["year"]])
        # Get or create payroll_month
        pm = db.scalar(select(PayrollMonth).where(
            PayrollMonth.financial_year_id == fy_id,
            PayrollMonth.month == month,
            PayrollMonth.year == year))
        if not pm:
            pm = PayrollMonth(financial_year_id=fy_id, month=month, year=year,
                              status=PayrollStatus.LOCKED.value, working_days=30,
                              remarks="Imported historical data")
            db.add(pm); db.flush()
        # Get latest active structure or fallback
        struct = db.scalar(select(SalaryStructure).where(
            SalaryStructure.employee_id == emp.id).order_by(SalaryStructure.id.desc()))
        if not struct:
            errors.append({"row": row_idx, "error": f"No salary structure for {emp.emp_code}"})
            continue
        rec = PayrollRecord(
            payroll_month_id=pm.id, employee_id=emp.id, salary_structure_id=struct.id,
            working_days=30, paid_days=Decimal(30),
            basic=_dec(row[h["basic"]]), da=_dec(row[h["da"]]),
            hra=_dec(row[h["hra"]]), special_allowance=_dec(row[h["special_allowance"]]),
            other_allowance=_dec(row[h["other_allowance"]]),
            gross_salary=_dec(row[h["gross_salary"]]),
            epf_employee=_dec(row[h["epf_employee"]]),
            esi_employee=_dec(row[h["esi_employee"]]),
            tds=_dec(row[h["tds"]]),
            professional_tax=_dec(row[h["professional_tax"]]),
            lwf_employee=_dec(row[h["lwf_employee"]]),
            total_deductions=_dec(row[h["total_deductions"]]),
            net_salary=_dec(row[h["net_salary"]]),
            epf_employer=_dec(row[h["epf_employer"]]),
            esi_employer=_dec(row[h["esi_employer"]]),
            ctc=_dec(row[h["ctc"]]),
            status=PayrollStatus.LOCKED.value,
            data_source="IMPORTED",
        )
        db.add(rec)
        inserted += 1
    db.flush()
    return {"inserted": inserted, "errors": errors}
