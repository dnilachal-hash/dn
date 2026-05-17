"""Course and ProfessionalYear models."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Numeric, ForeignKey, Text
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_years: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, default=Decimal("5.5"))
    has_internship: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    professional_years: Mapped[list["ProfessionalYear"]] = relationship(
        "ProfessionalYear", back_populates="course", order_by="ProfessionalYear.sort_order"
    )


class ProfessionalYear(Base):
    __tablename__ = "professional_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey("courses.id"), nullable=False)
    year_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    is_internship: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="professional_years")
