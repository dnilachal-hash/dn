from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Numeric, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

M = Numeric(15, 2)


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)

    basic: Mapped[Decimal] = mapped_column(M, default=0)
    da: Mapped[Decimal] = mapped_column(M, default=0)
    hra: Mapped[Decimal] = mapped_column(M, default=0)
    medical_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    conveyance_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    transport_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    special_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    other_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    children_education_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    uniform_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    telephone_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    internet_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    research_allowance: Mapped[Decimal] = mapped_column(M, default=0)
    gross_monthly: Mapped[Decimal] = mapped_column(M, default=0)
    pf_wage_override: Mapped[Decimal | None] = mapped_column(M)

    status: Mapped[str] = mapped_column(String(20), default="DRAFT")  # DRAFT/ACTIVE/EXPIRED
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    custom_allowances = relationship("CustomAllowance", back_populates="salary_structure",
                                     cascade="all, delete-orphan")


class CustomAllowance(Base):
    __tablename__ = "custom_allowances"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    salary_structure_id: Mapped[int] = mapped_column(ForeignKey("salary_structures.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(M, default=0)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pf_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    salary_structure = relationship("SalaryStructure", back_populates="custom_allowances")


class SalaryRevision(Base):
    __tablename__ = "salary_revisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    old_structure_id: Mapped[int | None] = mapped_column(ForeignKey("salary_structures.id"))
    new_structure_id: Mapped[int] = mapped_column(ForeignKey("salary_structures.id"))
    revision_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    revised_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmployeeTaxDeclaration(Base):
    __tablename__ = "employee_tax_declarations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    tax_regime: Mapped[str] = mapped_column(String(10), default="NEW")  # OLD/NEW

    hra_rent_paid: Mapped[Decimal] = mapped_column(M, default=0)
    hra_city_tier: Mapped[str] = mapped_column(String(20), default="NON_METRO")

    sec_80c: Mapped[Decimal] = mapped_column(M, default=0)
    sec_80d: Mapped[Decimal] = mapped_column(M, default=0)
    sec_80g: Mapped[Decimal] = mapped_column(M, default=0)
    sec_80e: Mapped[Decimal] = mapped_column(M, default=0)
    nps_80ccd1b: Mapped[Decimal] = mapped_column(M, default=0)
    other_deductions: Mapped[dict | None] = mapped_column(JSON)

    previous_employer_income: Mapped[Decimal] = mapped_column(M, default=0)
    previous_employer_tds: Mapped[Decimal] = mapped_column(M, default=0)
    form_12b_received: Mapped[bool] = mapped_column(Boolean, default=False)

    declaration_submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
