"""Fee structure, heads, and assignment models."""
import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Text, Numeric,
    Enum as SAEnum, ForeignKey,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class FeeType(str, enum.Enum):
    TUITION = "TUITION"
    EXAM = "EXAM"
    HOSTEL = "HOSTEL"
    TRANSPORT = "TRANSPORT"
    REGISTRATION = "REGISTRATION"
    LIBRARY = "LIBRARY"
    LAB = "LAB"
    MISC = "MISC"
    REFUND = "REFUND"
    CONCESSION = "CONCESSION"
    OTHER = "OTHER"


class FeeFrequency(str, enum.Enum):
    ONE_TIME = "ONE_TIME"
    YEARLY = "YEARLY"
    SEMESTER = "SEMESTER"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class FeeHead(Base):
    __tablename__ = "fee_heads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    fee_type: Mapped[FeeType] = mapped_column(
        SAEnum(FeeType, name="feetype"), nullable=False, default=FeeType.OTHER
    )
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frequency: Mapped[FeeFrequency] = mapped_column(
        SAEnum(FeeFrequency, name="feefrequency"), nullable=False, default=FeeFrequency.YEARLY
    )
    is_compulsory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    structure_items: Mapped[list["FeeStructureItem"]] = relationship(
        "FeeStructureItem", back_populates="fee_head"
    )


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    batch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("batches.id"), nullable=True, index=True
    )
    academic_session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=True
    )
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    course: Mapped["app.models.student.Course"] = relationship("Course")
    batch: Mapped[Optional["app.models.student.Batch"]] = relationship("Batch")
    academic_session: Mapped[Optional["app.models.student.AcademicSession"]] = relationship(
        "AcademicSession"
    )
    financial_year: Mapped["app.models.org.FinancialYear"] = relationship("FinancialYear")
    creator: Mapped[Optional["app.models.user.User"]] = relationship(
        "User", foreign_keys=[created_by]
    )
    items: Mapped[list["FeeStructureItem"]] = relationship(
        "FeeStructureItem", back_populates="fee_structure", cascade="all, delete-orphan"
    )


class FeeStructureItem(Base):
    __tablename__ = "fee_structure_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fee_structure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fee_head_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fee_heads.id"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_compulsory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="items")
    fee_head: Mapped["FeeHead"] = relationship("FeeHead", back_populates="structure_items")


class StudentFeeAssignment(Base):
    __tablename__ = "student_fee_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), nullable=False, index=True
    )
    fee_structure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fee_structures.id"), nullable=False
    )
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student: Mapped["app.models.student.Student"] = relationship("Student")
    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure")
    financial_year: Mapped["app.models.org.FinancialYear"] = relationship("FinancialYear")


class StudentFeeOverride(Base):
    __tablename__ = "student_fee_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id"), nullable=False, index=True
    )
    fee_head_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fee_heads.id"), nullable=False
    )
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False
    )
    override_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    student: Mapped["app.models.student.Student"] = relationship("Student")
    fee_head: Mapped["FeeHead"] = relationship("FeeHead")
    financial_year: Mapped["app.models.org.FinancialYear"] = relationship("FinancialYear")
