from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

M = Numeric(15, 2)


class EmployeeLoan(Base):
    __tablename__ = "employee_loans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), index=True)
    loan_type: Mapped[str] = mapped_column(String(40))  # LOAN/ADVANCE
    principal_amount: Mapped[Decimal] = mapped_column(M, default=0)
    emi_amount: Mapped[Decimal] = mapped_column(M, default=0)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0)
    start_month: Mapped[int] = mapped_column(Integer)
    start_year: Mapped[int] = mapped_column(Integer)
    total_installments: Mapped[int] = mapped_column(Integer, default=1)
    paid_installments: Mapped[int] = mapped_column(Integer, default=0)
    outstanding_balance: Mapped[Decimal] = mapped_column(M, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE/CLOSED/CANCELLED
    sanctioned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    sanctioned_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoanTransaction(Base):
    __tablename__ = "loan_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("employee_loans.id"))
    payroll_record_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_records.id"))
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    emi_deducted: Mapped[Decimal] = mapped_column(M, default=0)
    outstanding_after: Mapped[Decimal] = mapped_column(M, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
