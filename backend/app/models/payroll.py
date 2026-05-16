from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Numeric, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

M = Numeric(15, 2)


class PayrollStatus(str, PyEnum):
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"
    PAID = "PAID"


class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"


class PayrollMonth(Base):
    __tablename__ = "payroll_months"
    __table_args__ = (
        UniqueConstraint("financial_year_id", "month", "year", name="uq_payroll_month"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    financial_year_id: Mapped[int] = mapped_column(ForeignKey("financial_years.id"))
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PayrollStatus.DRAFT.value, index=True)
    working_days: Mapped[int] = mapped_column(Integer, default=30)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime)
    generated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime)
    locked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    unlock_reason: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    records = relationship("PayrollRecord", back_populates="payroll_month", cascade="all, delete-orphan")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    __table_args__ = (
        UniqueConstraint("payroll_month_id", "employee_id", name="uq_payroll_emp"),
        Index("ix_payroll_emp_month", "employee_id", "payroll_month_id"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_month_id: Mapped[int] = mapped_column(ForeignKey("payroll_months.id", ondelete="CASCADE"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    salary_structure_id: Mapped[int] = mapped_column(ForeignKey("salary_structures.id"))

    working_days: Mapped[int] = mapped_column(Integer, default=30)
    paid_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30.00"))
    lop_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    is_new_joiner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_exit_month: Mapped[bool] = mapped_column(Boolean, default=False)

    # Earnings
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
    overtime_pay: Mapped[Decimal] = mapped_column(M, default=0)
    bonus: Mapped[Decimal] = mapped_column(M, default=0)
    arrears: Mapped[Decimal] = mapped_column(M, default=0)
    reimbursement: Mapped[Decimal] = mapped_column(M, default=0)
    gross_salary: Mapped[Decimal] = mapped_column(M, default=0)

    # Employee Deductions
    pf_wage: Mapped[Decimal] = mapped_column(M, default=0)
    epf_employee: Mapped[Decimal] = mapped_column(M, default=0)
    esi_wage: Mapped[Decimal] = mapped_column(M, default=0)
    esi_employee: Mapped[Decimal] = mapped_column(M, default=0)
    tds: Mapped[Decimal] = mapped_column(M, default=0)
    professional_tax: Mapped[Decimal] = mapped_column(M, default=0)
    lwf_employee: Mapped[Decimal] = mapped_column(M, default=0)
    loan_emi: Mapped[Decimal] = mapped_column(M, default=0)
    advance_recovery: Mapped[Decimal] = mapped_column(M, default=0)
    other_deductions: Mapped[Decimal] = mapped_column(M, default=0)
    total_deductions: Mapped[Decimal] = mapped_column(M, default=0)
    net_salary: Mapped[Decimal] = mapped_column(M, default=0)

    # Employer
    epf_employer: Mapped[Decimal] = mapped_column(M, default=0)
    eps: Mapped[Decimal] = mapped_column(M, default=0)
    edli: Mapped[Decimal] = mapped_column(M, default=0)
    epf_admin: Mapped[Decimal] = mapped_column(M, default=0)
    esi_employer: Mapped[Decimal] = mapped_column(M, default=0)
    lwf_employer: Mapped[Decimal] = mapped_column(M, default=0)
    gratuity_provision: Mapped[Decimal] = mapped_column(M, default=0)
    bonus_provision: Mapped[Decimal] = mapped_column(M, default=0)
    employer_total: Mapped[Decimal] = mapped_column(M, default=0)
    ctc: Mapped[Decimal] = mapped_column(M, default=0)

    status: Mapped[str] = mapped_column(String(20), default=PayrollStatus.GENERATED.value)
    payment_status: Mapped[str] = mapped_column(String(20), default=PaymentStatus.PENDING.value)
    payment_date: Mapped[date | None] = mapped_column(Date)
    payment_reference: Mapped[str | None] = mapped_column(String(80))
    remarks: Mapped[str | None] = mapped_column(Text)
    data_source: Mapped[str] = mapped_column(String(20), default="LIVE")  # LIVE / IMPORTED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payroll_month = relationship("PayrollMonth", back_populates="records")
    employee = relationship("Employee")
    custom_components = relationship("PayrollCustomComponent", back_populates="payroll_record",
                                     cascade="all, delete-orphan")


class PayrollCustomComponent(Base):
    __tablename__ = "payroll_custom_components"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payroll_record_id: Mapped[int] = mapped_column(ForeignKey("payroll_records.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(M, default=0)
    type: Mapped[str] = mapped_column(String(20))  # EARNING / DEDUCTION
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    payroll_record = relationship("PayrollRecord", back_populates="custom_components")
