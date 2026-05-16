from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_path: Mapped[str | None] = mapped_column(String(500))
    pan: Mapped[str | None] = mapped_column(String(10))
    tan: Mapped[str | None] = mapped_column(String(10))
    gstin: Mapped[str | None] = mapped_column(String(15))
    epf_establishment_code: Mapped[str | None] = mapped_column(String(20))
    esi_establishment_code: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    state_code: Mapped[str | None] = mapped_column(String(5))
    city: Mapped[str | None] = mapped_column(String(80))
    city_tier: Mapped[str] = mapped_column(String(20), default="NON_METRO")
    pin: Mapped[str | None] = mapped_column(String(10))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(120))
    financial_year_start_month: Mapped[int] = mapped_column(Integer, default=4)
    nch_registration_no: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FinancialYear(Base):
    __tablename__ = "financial_years"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year_label: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # "2024-25"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    tax_year_label: Mapped[str] = mapped_column(String(10))  # "AY 2025-26"
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
