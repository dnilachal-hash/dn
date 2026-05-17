"""Organisation, FinancialYear, PaymentMode models."""
import enum
from datetime import datetime, date
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Date, Enum as SAEnum, Text, Numeric
)
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base


class ReceiptNumberingFormat(str, enum.Enum):
    SIMPLE = "SIMPLE"
    PREFIXED = "PREFIXED"


class Organisation(Base):
    __tablename__ = "organisation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    website: Mapped[str | None] = mapped_column(String(256), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    receipt_header: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_footer: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_numbering_format: Mapped[ReceiptNumberingFormat] = mapped_column(
        SAEnum(ReceiptNumberingFormat), default=ReceiptNumberingFormat.SIMPLE, nullable=False
    )
    gstin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    principal_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class FinancialYear(Base):
    __tablename__ = "financial_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_receipt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_exam_receipt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_library_receipt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PaymentMode(Base):
    __tablename__ = "payment_modes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
