from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

M = Numeric(15, 2)


class TDSCalculation(Base):
    __tablename__ = "tds_calculations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_record_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_records.id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)

    projected_annual_gross: Mapped[Decimal] = mapped_column(M, default=0)
    hra_exemption: Mapped[Decimal] = mapped_column(M, default=0)
    standard_deduction: Mapped[Decimal] = mapped_column(M, default=0)
    chapter_via_deduction: Mapped[Decimal] = mapped_column(M, default=0)
    taxable_income: Mapped[Decimal] = mapped_column(M, default=0)
    tax_old_regime: Mapped[Decimal] = mapped_column(M, default=0)
    tax_new_regime: Mapped[Decimal] = mapped_column(M, default=0)
    tax_regime_applied: Mapped[str] = mapped_column(String(10))
    surcharge: Mapped[Decimal] = mapped_column(M, default=0)
    cess: Mapped[Decimal] = mapped_column(M, default=0)
    rebate: Mapped[Decimal] = mapped_column(M, default=0)
    annual_tax: Mapped[Decimal] = mapped_column(M, default=0)
    tds_to_date: Mapped[Decimal] = mapped_column(M, default=0)
    remaining_months: Mapped[int] = mapped_column(Integer, default=12)
    monthly_tds: Mapped[Decimal] = mapped_column(M, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
