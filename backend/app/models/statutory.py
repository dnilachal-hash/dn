from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

M = Numeric(15, 2)
P = Numeric(6, 4)


class EPFSetting(Base):
    __tablename__ = "epf_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"), unique=True)
    employee_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("12.0000"))
    employer_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("12.0000"))
    eps_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("8.3300"))
    eps_wage_ceiling: Mapped[Decimal] = mapped_column(M, default=Decimal("15000.00"))
    edli_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("0.5000"))
    edli_wage_ceiling: Mapped[Decimal] = mapped_column(M, default=Decimal("15000.00"))
    admin_charge_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("0.5000"))
    pf_wage_ceiling: Mapped[Decimal] = mapped_column(M, default=Decimal("15000.00"))
    voluntary_pf_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    applicable_from: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ESISetting(Base):
    __tablename__ = "esi_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"), unique=True)
    employee_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("0.7500"))
    employer_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("3.2500"))
    wage_ceiling: Mapped[Decimal] = mapped_column(M, default=Decimal("21000.00"))
    applicable_from: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PTStateSetting(Base):
    __tablename__ = "pt_state_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(5), nullable=False)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    slabs: Mapped[list] = mapped_column(JSON)  # [{"min":0,"max":15000,"amount":0}, ...]
    periodicity: Mapped[str] = mapped_column(String(20), default="MONTHLY")
    applicable_from: Mapped[date] = mapped_column(Date, default=date.today)


class LWFSetting(Base):
    __tablename__ = "lwf_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(5), nullable=False)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    employee_amount: Mapped[Decimal] = mapped_column(M, default=0)
    employer_amount: Mapped[Decimal] = mapped_column(M, default=0)
    periodicity: Mapped[str] = mapped_column(String(20), default="MONTHLY")  # MONTHLY/SEMI_ANNUAL/ANNUAL
    applicable_from: Mapped[date] = mapped_column(Date, default=date.today)


class MinimumWageSetting(Base):
    __tablename__ = "minimum_wage_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(5), nullable=False)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    category: Mapped[str] = mapped_column(String(60))
    skill_level: Mapped[str] = mapped_column(String(30))  # UNSKILLED/SEMI_SKILLED/SKILLED/HIGHLY_SKILLED
    daily_rate: Mapped[Decimal] = mapped_column(M, default=0)
    monthly_rate: Mapped[Decimal] = mapped_column(M, default=0)
    applicable_from: Mapped[date] = mapped_column(Date, default=date.today)


class TDSSetting(Base):
    __tablename__ = "tds_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"), unique=True)
    tax_regime_default: Mapped[str] = mapped_column(String(10), default="NEW")
    standard_deduction_old: Mapped[Decimal] = mapped_column(M, default=Decimal("50000.00"))
    standard_deduction_new: Mapped[Decimal] = mapped_column(M, default=Decimal("75000.00"))
    basic_exemption_old: Mapped[Decimal] = mapped_column(M, default=Decimal("250000.00"))
    basic_exemption_new: Mapped[Decimal] = mapped_column(M, default=Decimal("300000.00"))
    cess_rate: Mapped[Decimal] = mapped_column(P, default=Decimal("4.0000"))
    # JSON: [{"upto": 250000, "rate": 0}, {"upto": 500000, "rate": 5}, ...]
    tax_slabs_old: Mapped[list] = mapped_column(JSON)
    tax_slabs_new: Mapped[list] = mapped_column(JSON)
    surcharge_slabs: Mapped[list] = mapped_column(JSON)
    rebate_87a_limit_old: Mapped[Decimal] = mapped_column(M, default=Decimal("500000.00"))
    rebate_87a_amount_old: Mapped[Decimal] = mapped_column(M, default=Decimal("12500.00"))
    rebate_87a_limit_new: Mapped[Decimal] = mapped_column(M, default=Decimal("700000.00"))
    rebate_87a_amount_new: Mapped[Decimal] = mapped_column(M, default=Decimal("25000.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
