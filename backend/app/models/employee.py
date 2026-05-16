from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="TEACHING")  # TEACHING / NON_TEACHING
    description: Mapped[str | None] = mapped_column(Text)
    nch_code: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    designations = relationship("Designation", back_populates="department", cascade="all, delete-orphan")


class Designation(Base):
    __tablename__ = "designations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    category: Mapped[str | None] = mapped_column(String(80))
    is_teaching: Mapped[bool] = mapped_column(Boolean, default=False)
    min_wage_category: Mapped[str | None] = mapped_column(String(60))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    department = relationship("Department", back_populates="designations")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_dept_active", "department_id", "is_active"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    emp_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(80))
    email: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    dob: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(10))
    marital_status: Mapped[str | None] = mapped_column(String(20))
    father_name: Mapped[str | None] = mapped_column(String(120))
    mother_name: Mapped[str | None] = mapped_column(String(120))
    spouse_name: Mapped[str | None] = mapped_column(String(120))
    address: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(String(60))

    # Encrypted PII
    pan_encrypted: Mapped[str | None] = mapped_column(String(500))
    aadhaar_encrypted: Mapped[str | None] = mapped_column(String(500))
    uan: Mapped[str | None] = mapped_column(String(20))
    esi_ip_number: Mapped[str | None] = mapped_column(String(20))

    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    designation_id: Mapped[int | None] = mapped_column(ForeignKey("designations.id"))
    date_of_joining: Mapped[date | None] = mapped_column(Date)
    date_of_exit: Mapped[date | None] = mapped_column(Date)
    employment_type: Mapped[str] = mapped_column(String(20), default="PERMANENT")  # PERMANENT/CONTRACT/PROBATION
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    epf_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    esi_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    pt_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    lwf_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=True)

    city_tier: Mapped[str] = mapped_column(String(20), default="NON_METRO")  # METRO/NON_METRO
    state_for_pt: Mapped[str | None] = mapped_column(String(5))
    photo_path: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department")
    designation = relationship("Designation")
    bank_details = relationship("EmployeeBankDetail", back_populates="employee", cascade="all, delete-orphan")


class EmployeeBankDetail(Base):
    __tablename__ = "employee_bank_details"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"))
    account_number_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    ifsc: Mapped[str] = mapped_column(String(11), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(120))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    employee = relationship("Employee", back_populates="bank_details")
