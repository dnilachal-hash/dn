from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from .common import BaseSchema


class CustomAllowanceIn(BaseModel):
    name: str
    amount: Decimal
    is_taxable: bool = True
    is_pf_eligible: bool = False


class CustomAllowanceOut(BaseSchema, CustomAllowanceIn):
    id: int


class SalaryStructureBase(BaseModel):
    employee_id: int
    financial_year_id: int
    effective_from: date
    effective_to: date | None = None
    basic: Decimal = Decimal(0)
    da: Decimal = Decimal(0)
    hra: Decimal = Decimal(0)
    medical_allowance: Decimal = Decimal(0)
    conveyance_allowance: Decimal = Decimal(0)
    transport_allowance: Decimal = Decimal(0)
    special_allowance: Decimal = Decimal(0)
    other_allowance: Decimal = Decimal(0)
    children_education_allowance: Decimal = Decimal(0)
    uniform_allowance: Decimal = Decimal(0)
    telephone_allowance: Decimal = Decimal(0)
    internet_allowance: Decimal = Decimal(0)
    research_allowance: Decimal = Decimal(0)
    pf_wage_override: Decimal | None = None


class SalaryStructureCreate(SalaryStructureBase):
    custom_allowances: list[CustomAllowanceIn] = []


class SalaryStructureOut(BaseSchema, SalaryStructureBase):
    id: int
    gross_monthly: Decimal
    status: str
    custom_allowances: list[CustomAllowanceOut] = []
    created_at: datetime


class TaxDeclarationIn(BaseModel):
    employee_id: int
    financial_year_id: int
    tax_regime: str = "NEW"
    hra_rent_paid: Decimal = Decimal(0)
    hra_city_tier: str = "NON_METRO"
    sec_80c: Decimal = Decimal(0)
    sec_80d: Decimal = Decimal(0)
    sec_80g: Decimal = Decimal(0)
    sec_80e: Decimal = Decimal(0)
    nps_80ccd1b: Decimal = Decimal(0)
    other_deductions: dict | None = None
    previous_employer_income: Decimal = Decimal(0)
    previous_employer_tds: Decimal = Decimal(0)
    form_12b_received: bool = False


class TaxDeclarationOut(BaseSchema, TaxDeclarationIn):
    id: int
    verified_at: datetime | None
