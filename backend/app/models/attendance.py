from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base

M = Numeric(15, 2)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "month", "year", name="uq_attendance_emp_mo"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    month: Mapped[int] = mapped_column(Integer)
    year: Mapped[int] = mapped_column(Integer)
    working_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30"))
    present_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30"))
    lop_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    leave_paid: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    leave_unpaid: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReimbursementClaim(Base):
    __tablename__ = "reimbursement_claims"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    claim_date: Mapped[date] = mapped_column(Date, default=date.today)
    category: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(M, default=0)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING/APPROVED/REJECTED/PAID
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    payroll_record_id: Mapped[int | None] = mapped_column(ForeignKey("payroll_records.id"))
    remarks: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
