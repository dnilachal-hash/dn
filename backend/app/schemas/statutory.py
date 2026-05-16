from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from .common import BaseSchema


class EPFSettingIn(BaseModel):
    financial_year_id: int
    employee_rate: Decimal = Decimal("12")
    employer_rate: Decimal = Decimal("12")
    eps_rate: Decimal = Decimal("8.33")
    eps_wage_ceiling: Decimal = Decimal("15000")
    edli_rate: Decimal = Decimal("0.5")
    edli_wage_ceiling: Decimal = Decimal("15000")
    admin_charge_rate: Decimal = Decimal("0.5")
    pf_wage_ceiling: Decimal = Decimal("15000")
    voluntary_pf_allowed: bool = True
    applicable_from: date


class EPFSettingOut(BaseSchema, EPFSettingIn):
    id: int


class ESISettingIn(BaseModel):
    financial_year_id: int
    employee_rate: Decimal = Decimal("0.75")
    employer_rate: Decimal = Decimal("3.25")
    wage_ceiling: Decimal = Decimal("21000")
    applicable_from: date


class ESISettingOut(BaseSchema, ESISettingIn):
    id: int


class PTSlab(BaseModel):
    min: Decimal
    max: Decimal | None
    amount: Decimal


class PTSettingIn(BaseModel):
    state_code: str
    financial_year_id: int
    slabs: list[PTSlab]
    periodicity: str = "MONTHLY"
    applicable_from: date


class PTSettingOut(BaseSchema, PTSettingIn):
    id: int


class LWFSettingIn(BaseModel):
    state_code: str
    financial_year_id: int
    employee_amount: Decimal
    employer_amount: Decimal
    periodicity: str = "MONTHLY"
    applicable_from: date


class LWFSettingOut(BaseSchema, LWFSettingIn):
    id: int


class TDSSlab(BaseModel):
    upto: Decimal  # 0 means no cap (highest slab)
    rate: Decimal  # percentage


class TDSSettingIn(BaseModel):
    financial_year_id: int
    tax_regime_default: str = "NEW"
    standard_deduction_old: Decimal = Decimal("50000")
    standard_deduction_new: Decimal = Decimal("75000")
    basic_exemption_old: Decimal = Decimal("250000")
    basic_exemption_new: Decimal = Decimal("300000")
    cess_rate: Decimal = Decimal("4")
    tax_slabs_old: list[TDSSlab]
    tax_slabs_new: list[TDSSlab]
    surcharge_slabs: list[dict]
    rebate_87a_limit_old: Decimal = Decimal("500000")
    rebate_87a_amount_old: Decimal = Decimal("12500")
    rebate_87a_limit_new: Decimal = Decimal("700000")
    rebate_87a_amount_new: Decimal = Decimal("25000")


class TDSSettingOut(BaseSchema, TDSSettingIn):
    id: int
