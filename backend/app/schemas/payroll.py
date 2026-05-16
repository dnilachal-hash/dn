from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from .common import BaseSchema


class PayrollMonthCreate(BaseModel):
    financial_year_id: int
    month: int
    year: int
    working_days: int = 30
    remarks: str | None = None


class PayrollMonthOut(BaseSchema):
    id: int
    financial_year_id: int
    month: int
    year: int
    status: str
    working_days: int
    generated_at: datetime | None
    approved_at: datetime | None
    locked_at: datetime | None
    remarks: str | None


class PayrollGenerateRequest(BaseModel):
    employee_ids: list[int] | None = None
    department_id: int | None = None
    recalculate_tds: bool = True


class PayrollRecordOut(BaseSchema):
    id: int
    payroll_month_id: int
    employee_id: int
    salary_structure_id: int
    working_days: int
    paid_days: Decimal
    lop_days: Decimal
    basic: Decimal
    da: Decimal
    hra: Decimal
    medical_allowance: Decimal
    conveyance_allowance: Decimal
    transport_allowance: Decimal
    special_allowance: Decimal
    other_allowance: Decimal
    children_education_allowance: Decimal
    uniform_allowance: Decimal
    telephone_allowance: Decimal
    internet_allowance: Decimal
    research_allowance: Decimal
    overtime_pay: Decimal
    bonus: Decimal
    arrears: Decimal
    reimbursement: Decimal
    gross_salary: Decimal
    pf_wage: Decimal
    epf_employee: Decimal
    esi_wage: Decimal
    esi_employee: Decimal
    tds: Decimal
    professional_tax: Decimal
    lwf_employee: Decimal
    loan_emi: Decimal
    advance_recovery: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_salary: Decimal
    epf_employer: Decimal
    eps: Decimal
    edli: Decimal
    epf_admin: Decimal
    esi_employer: Decimal
    lwf_employer: Decimal
    gratuity_provision: Decimal
    bonus_provision: Decimal
    employer_total: Decimal
    ctc: Decimal
    status: str
    payment_status: str
    payment_date: date | None
    remarks: str | None
    data_source: str
    created_at: datetime


class UnlockRequest(BaseModel):
    reason: str


class MarkPaidRequest(BaseModel):
    payment_date: date
    payment_reference: str | None = None
