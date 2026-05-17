"""AcademicSession and StudentEnrollment models.
Named session_model.py to avoid collision with Python's session module.
"""
import enum
from datetime import datetime, date
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Date, Enum as SAEnum,
    ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DETAINED = "DETAINED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AcademicSession(Base):
    __tablename__ = "academic_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    financial_year_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    enrollments: Mapped[list["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="academic_session"
    )


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    academic_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=False
    )
    professional_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("professional_years.id"), nullable=False
    )
    roll_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "academic_session_id", name="uq_student_session"),
    )

    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    academic_session: Mapped["AcademicSession"] = relationship(
        "AcademicSession", back_populates="enrollments"
    )
    professional_year: Mapped["ProfessionalYear"] = relationship("ProfessionalYear")


# Avoid circular import — Student is defined in student.py
from app.models.course import ProfessionalYear  # noqa: E402, F401
