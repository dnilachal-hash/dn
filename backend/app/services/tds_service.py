"""TDS Calculation Engine — 16-step pipeline."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, extract

from ..models.salary import SalaryStructure, EmployeeTaxDeclaration
from ..models.statutory import TDSSetting
from ..models.payroll import PayrollRecord, PayrollMonth
from ..models.employee import Employee
from ..models.org import FinancialYear
from ..models.tds import TDSCalculation

ZERO = Decimal("0.00")


def _q(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _months_remaining_in_fy(month: int, year: int, fy: FinancialYear) -> int:
    """How many months including current month are left until end of FY."""
    end_year = fy.end_date.year
    end_month = fy.end_date.month
    return (end_year - year) * 12 + (end_month - month) + 1


def _apply_slabs(income: Decimal, slabs: list[dict]) -> Decimal:
    """Apply slab list of form [{upto: X, rate: pct}, ...]. upto=0 means no upper cap."""
    tax = Decimal(0)
    previous = Decimal(0)
    for slab in slabs:
        upto = Decimal(str(slab.get("upto") or 0))
        rate = Decimal(str(slab.get("rate") or 0)) / Decimal(100)
        if upto == 0 or income <= upto:
            taxable_in_slab = max(Decimal(0), income - previous)
            tax += taxable_in_slab * rate
            return tax
        else:
            taxable_in_slab = upto - previous
            tax += taxable_in_slab * rate
            previous = upto
    return tax


def _apply_surcharge(income: Decimal, tax: Decimal, surcharge_slabs: list[dict]) -> Decimal:
    """Surcharge slab: [{above: 5000000, rate: 10}, ...]"""
    for slab in surcharge_slabs:
        above = Decimal(str(slab.get("above") or 0))
        rate = Decimal(str(slab.get("rate") or 0)) / Decimal(100)
        if income > above:
            return tax * rate
    return Decimal(0)


def _hra_exemption(annual_basic_da: Decimal, annual_hra: Decimal,
                   annual_rent: Decimal, is_metro: bool) -> Decimal:
    """min(actual_hra, [50/40]% of basic+da, rent - 10% of basic+da)."""
    if annual_hra <= 0 or annual_rent <= 0:
        return Decimal(0)
    pct = Decimal("0.50") if is_metro else Decimal("0.40")
    pct_of_basic = annual_basic_da * pct
    rent_excess = annual_rent - (annual_basic_da * Decimal("0.10"))
    rent_excess = max(rent_excess, Decimal(0))
    return min(annual_hra, pct_of_basic, rent_excess)


def calculate_tds(db: Session, employee_id: int, month: int, year: int) -> dict:
    """Full 16-step TDS computation. Returns dict with monthly_tds and all components."""
    emp = db.get(Employee, employee_id)
    if not emp or not emp.tds_applicable:
        return {"monthly_tds": ZERO, "skipped": True, "reason": "TDS not applicable"}

    # Determine FY
    fy = db.scalar(select(FinancialYear).where(
        and_(FinancialYear.start_date <= date(year, month, 1),
             FinancialYear.end_date >= date(year, month, 1))
    ))
    if not fy:
        return {"monthly_tds": ZERO, "skipped": True, "reason": "No FY configured"}

    settings = db.scalar(select(TDSSetting).where(TDSSetting.financial_year_id == fy.id))
    if not settings:
        return {"monthly_tds": ZERO, "skipped": True, "reason": "No TDS settings for FY"}

    declaration = db.scalar(select(EmployeeTaxDeclaration).where(
        and_(EmployeeTaxDeclaration.employee_id == employee_id,
             EmployeeTaxDeclaration.financial_year_id == fy.id)
    ))
    regime = declaration.tax_regime if declaration else settings.tax_regime_default

    # Active salary structure
    structure = db.scalar(select(SalaryStructure).where(
        and_(SalaryStructure.employee_id == employee_id,
             SalaryStructure.status == "ACTIVE",
             SalaryStructure.effective_from <= date(year, month, 1))
    ).order_by(SalaryStructure.effective_from.desc()))
    if not structure:
        return {"monthly_tds": ZERO, "skipped": True, "reason": "No salary structure"}

    monthly_gross = Decimal(structure.gross_monthly or 0)
    monthly_basic_da = Decimal(structure.basic or 0) + Decimal(structure.da or 0)
    monthly_hra = Decimal(structure.hra or 0)

    # Step 1: projected annual gross
    remaining_months = _months_remaining_in_fy(month, year, fy)
    past_months_in_fy = 12 - remaining_months

    past_gross = db.scalar(
        select(PayrollRecord.gross_salary).join(PayrollMonth).where(
            and_(PayrollRecord.employee_id == employee_id,
                 PayrollMonth.financial_year_id == fy.id,
                 ~((PayrollMonth.month == month) & (PayrollMonth.year == year)))
        )
    ) or Decimal(0)
    # Sum past actually-paid gross
    from sqlalchemy import func
    past_gross_total = db.scalar(
        select(func.coalesce(func.sum(PayrollRecord.gross_salary), 0)).join(PayrollMonth).where(
            and_(PayrollRecord.employee_id == employee_id,
                 PayrollMonth.financial_year_id == fy.id,
                 ~((PayrollMonth.month == month) & (PayrollMonth.year == year)))
        )
    ) or Decimal(0)
    past_gross_total = Decimal(past_gross_total)

    projected_gross = past_gross_total + (monthly_gross * Decimal(remaining_months))

    # Step 2: add previous employer income
    if declaration:
        projected_gross += Decimal(declaration.previous_employer_income or 0)

    # Step 3: HRA exemption (only in OLD regime)
    annual_basic_da = monthly_basic_da * Decimal(12)
    annual_hra = monthly_hra * Decimal(12)
    annual_rent = Decimal(declaration.hra_rent_paid * 12 if declaration else 0)
    is_metro = (declaration.hra_city_tier == "METRO") if declaration else (emp.city_tier == "METRO")
    hra_exempt = _hra_exemption(annual_basic_da, annual_hra, annual_rent, is_metro) if regime == "OLD" else Decimal(0)

    # Step 4-6: deductions
    pt_total = db.scalar(
        select(func.coalesce(func.sum(PayrollRecord.professional_tax), 0)).join(PayrollMonth).where(
            and_(PayrollRecord.employee_id == employee_id,
                 PayrollMonth.financial_year_id == fy.id)
        )
    ) or Decimal(0)

    std_deduction = Decimal(settings.standard_deduction_new if regime == "NEW" else settings.standard_deduction_old)

    chapter_via = Decimal(0)
    if regime == "OLD" and declaration:
        chapter_via = min(Decimal("150000"), Decimal(declaration.sec_80c or 0))
        chapter_via += min(Decimal("100000"), Decimal(declaration.sec_80d or 0))
        chapter_via += Decimal(declaration.sec_80g or 0)
        chapter_via += Decimal(declaration.sec_80e or 0)
        chapter_via += min(Decimal("50000"), Decimal(declaration.nps_80ccd1b or 0))

    # Step 7: taxable income
    taxable = projected_gross - hra_exempt - Decimal(pt_total) - std_deduction - chapter_via
    taxable = max(taxable, Decimal(0))

    # Step 8: apply slabs
    slabs = settings.tax_slabs_new if regime == "NEW" else settings.tax_slabs_old
    tax = _apply_slabs(taxable, slabs)

    # Step 9: surcharge
    surcharge = _apply_surcharge(taxable, tax, settings.surcharge_slabs or [])

    # Step 10: cess
    cess_rate = Decimal(settings.cess_rate or 0) / Decimal(100)
    cess = (tax + surcharge) * cess_rate

    # Step 11: rebate u/s 87A
    rebate = Decimal(0)
    if regime == "OLD" and taxable <= Decimal(settings.rebate_87a_limit_old or 0):
        rebate = min(tax, Decimal(settings.rebate_87a_amount_old or 0))
    elif regime == "NEW" and taxable <= Decimal(settings.rebate_87a_limit_new or 0):
        rebate = min(tax, Decimal(settings.rebate_87a_amount_new or 0))

    annual_tax = max(tax - rebate, Decimal(0)) + surcharge + cess

    # Step 13-14: subtract TDS already deducted
    tds_to_date = db.scalar(
        select(func.coalesce(func.sum(PayrollRecord.tds), 0)).join(PayrollMonth).where(
            and_(PayrollRecord.employee_id == employee_id,
                 PayrollMonth.financial_year_id == fy.id,
                 ~((PayrollMonth.month == month) & (PayrollMonth.year == year)))
        )
    ) or Decimal(0)
    tds_to_date = Decimal(tds_to_date)
    prev_employer_tds = Decimal(declaration.previous_employer_tds if declaration else 0)

    # Step 15: monthly TDS
    remaining_tax = annual_tax - tds_to_date - prev_employer_tds
    monthly_tds = remaining_tax / Decimal(remaining_months) if remaining_months > 0 else Decimal(0)
    monthly_tds = max(monthly_tds, Decimal(0))

    # Compute tax under both regimes for reporting
    tax_old = _apply_slabs(max(projected_gross - std_deduction - chapter_via - hra_exempt - pt_total, Decimal(0)),
                           settings.tax_slabs_old)
    tax_new = _apply_slabs(max(projected_gross - Decimal(settings.standard_deduction_new), Decimal(0)),
                           settings.tax_slabs_new)

    return {
        "monthly_tds": _q(monthly_tds),
        "annual_tax": _q(annual_tax),
        "projected_annual_gross": _q(projected_gross),
        "hra_exemption": _q(hra_exempt),
        "standard_deduction": _q(std_deduction),
        "chapter_via_deduction": _q(chapter_via),
        "taxable_income": _q(taxable),
        "tax_old_regime": _q(tax_old),
        "tax_new_regime": _q(tax_new),
        "tax_regime_applied": regime,
        "surcharge": _q(surcharge),
        "cess": _q(cess),
        "rebate": _q(rebate),
        "tds_to_date": _q(tds_to_date),
        "remaining_months": remaining_months,
        "skipped": False,
    }
