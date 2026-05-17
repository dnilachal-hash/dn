"""Fee head, fee structure, and student fee ledger models."""
import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Enum as SAEnum,
    ForeignKey, Text, Numeric, UniqueConstraint
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class FeeType(str, enum.Enum):
    TUITION = "TUITION"
    EXAM = "EXAM"
    LIBRARY = "LIBRARY"
    HOSTEL = "HOSTEL"
    TRANSPORT = "TRANSPORT"
    REGISTRATION = "REGISTRATION"
    DEVELOPMENT = "DEVELOPMENT"
    MISC = "MISC"
    CAUTION = "CAUTION"
    LATE_FEE = "LATE_FEE"
    FINE = "FINE"
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
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    fee_type: Mapped[FeeType] = mapped_column(SAEnum(FeeType), nullable=False)
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frequency: Mapped[FeeFrequency] = mapped_column(
        SAEnum(FeeFrequency), default=FeeFrequency.YEARLY, nullable=False
    )
    is_compulsory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    professional_year_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("professional_years.id"), nullable=True
    )
    academic_session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=True
    )
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    items: Mapped[list["FeeStructureItem"]] = relationship(
        "FeeStructureItem", back_populates="fee_structure",
        order_by="FeeStructureItem.sort_order"
    )
    course: Mapped["Course"] = relationship("Course")
    professional_year: Mapped["ProfessionalYear | None"] = relationship("ProfessionalYear")
    financial_year: Mapped["FinancialYear"] = relationship("FinancialYear")
    academic_session: Mapped["AcademicSession | None"] = relationship("AcademicSession")


class FeeStructureItem(Base):
    __tablename__ = "fee_structure_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fee_structure_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fee_structures.id"), nullable=False
    )
    fee_head_id: Mapped[int] = mapped_column(Integer, ForeignKey("fee_heads.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    is_compulsory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="items")
    fee_head: Mapped["FeeHead"] = relationship("FeeHead")


class StudentFeeLedger(Base):
    __tablename__ = "student_fee_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    fee_head_id: Mapped[int] = mapped_column(Integer, ForeignKey("fee_heads.id"), nullable=False)
    academic_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=False
    )
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False
    )
    amount_charged: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    amount_waived: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "fee_head_id", "academic_session_id", "financial_year_id",
            name="uq_ledger_entry"
        ),
    )

    student: Mapped["Student"] = relationship("Student")
    fee_head: Mapped["FeeHead"] = relationship("FeeHead")


from app.models.course import Course, ProfessionalYear  # noqa: E402, F401
from app.models.org import FinancialYear  # noqa: E402, F401
from app.models.session_model import AcademicSession  # noqa: E402, F401
from app.models.student import Student  # noqa: E402, F401
