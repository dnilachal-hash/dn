"""Student models."""
import enum
from datetime import datetime, date
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Date, Enum as SAEnum,
    ForeignKey, Text
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PASSED = "PASSED"
    DROPOUT = "DROPOUT"
    SUSPENDED = "SUSPENDED"
    TRANSFERRED = "TRANSFERRED"
    CANCELLED = "CANCELLED"


class GenderEnum(str, enum.Enum):
    M = "M"
    F = "F"
    O = "O"


class StudentCategory(Base):
    __tablename__ = "student_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    students: Mapped[list["Student"]] = relationship("Student", back_populates="category")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admission_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    father_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mother_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    guardian_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[GenderEnum | None] = mapped_column(SAEnum(GenderEnum), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("student_categories.id"), nullable=True
    )
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    batch_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enrollment_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    university_roll_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    student_status: Mapped[StudentStatus] = mapped_column(
        SAEnum(StudentStatus), default=StudentStatus.ACTIVE, nullable=False
    )
    is_hostel: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_transport: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scholarship_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    category: Mapped["StudentCategory | None"] = relationship("StudentCategory", back_populates="students")
    course: Mapped["Course"] = relationship("Course")
    enrollments: Mapped[list["StudentEnrollment"]] = relationship(
        "StudentEnrollment", back_populates="student", order_by="StudentEnrollment.id.desc()"
    )


from app.models.course import Course  # noqa: E402, F401
from app.models.session_model import StudentEnrollment  # noqa: E402, F401
