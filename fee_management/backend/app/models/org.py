"""Organisation, financial year, and payment mode models."""
import enum
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Date, Text,
    Enum as SAEnum, ForeignKey,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class ReceiptNumberingFormat(str, enum.Enum):
    SIMPLE = "SIMPLE"
    PREFIXED = "PREFIXED"


class PaymentModeCode(str, enum.Enum):
    CASH = "CASH"
    BANK = "BANK"
    CHEQUE = "CHEQUE"
    DD = "DD"
    UPI = "UPI"
    CARD = "CARD"
    OTHER = "OTHER"


class Organisation(Base):
    __tablename__ = "organisation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pin: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    logo_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    receipt_header: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_footer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_numbering_format: Mapped[ReceiptNumberingFormat] = mapped_column(
        SAEnum(ReceiptNumberingFormat, name="receiptnumberingformat"),
        default=ReceiptNumberingFormat.SIMPLE,
        nullable=False,
    )
    gstin: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class FinancialYear(Base):
    __tablename__ = "financial_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_receipt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PaymentMode(Base):
    __tablename__ = "payment_modes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[PaymentModeCode] = mapped_column(
        SAEnum(PaymentModeCode, name="paymentmodecode"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_reference: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_bank_name: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_date: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
