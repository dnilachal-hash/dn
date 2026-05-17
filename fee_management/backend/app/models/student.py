"""Student and academic structure models."""
import enum
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Date, Text,
    Enum as SAEnum, ForeignKey,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class Gender(str, enum.Enum):
    M = "M"
    F = "F"
    O = "O"


class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    DROPOUT = "DROPOUT"
    SUSPENDED = "SUSPENDED"
    TRANSFERRED = "TRANSFERRED"
    CANCELLED = "CANCELLED"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    batches: Mapped[list["Batch"]] = relationship("Batch", back_populates="course")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="course")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="batches")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="batch")


class AcademicSession(Base):
    __tablename__ = "academic_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    students: Mapped[list["Student"]] = relationship("Student", back_populates="academic_session")


class StudentCategory(Base):
    __tablename__ = "student_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    students: Mapped[list["Student"]] = relationship("Student", back_populates="category")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admission_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    father_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    mother_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    dob: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[Gender]] = mapped_column(
        SAEnum(Gender, name="gender"), nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("student_categories.id"), nullable=True
    )
    mobile: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pin: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    course_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("courses.id"), nullable=True, index=True
    )
    batch_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("batches.id"), nullable=True, index=True
    )
    academic_session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=True, index=True
    )
    professional_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    roll_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    enrollment_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    admission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    student_status: Mapped[StudentStatus] = mapped_column(
        SAEnum(StudentStatus, name="studentstatus"),
        default=StudentStatus.ACTIVE,
        nullable=False,
    )
    is_hostel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_transport: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scholarship_status: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    category: Mapped[Optional["StudentCategory"]] = relationship(
        "StudentCategory", back_populates="students"
    )
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="students")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="students")
    academic_session: Mapped[Optional["AcademicSession"]] = relationship(
        "AcademicSession", back_populates="students"
    )
    creator: Mapped[Optional["app.models.user.User"]] = relationship(
        "User", foreign_keys=[created_by]
    )
