"""Receipt, ReceiptItem, ReceiptPayment, and ReceiptCorrection models."""
import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, Integer, DateTime, Date, Enum as SAEnum,
    ForeignKey, Text, Numeric, JSON
)
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class ReceiptStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CORRECTED = "CORRECTED"
    CANCELLED = "CANCELLED"
    IMPORTED = "IMPORTED"
    MANUAL = "MANUAL"


class PaymentStatus(str, enum.Enum):
    CLEARED = "CLEARED"
    PENDING = "PENDING"
    BOUNCED = "BOUNCED"
    CANCELLED = "CANCELLED"


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    financial_year_id: Mapped[int] = mapped_column(Integer, ForeignKey("financial_years.id"), nullable=False)
    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id"), nullable=True)
    academic_session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("academic_sessions.id"), nullable=True
    )
    professional_year_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("professional_years.id"), nullable=True
    )
    # Denormalized for historical accuracy
    student_name: Mapped[str] = mapped_column(String(128), nullable=False)
    father_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    admission_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    course_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    professional_year_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_in_words: Mapped[str | None] = mapped_column(String(512), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReceiptStatus] = mapped_column(
        SAEnum(ReceiptStatus), default=ReceiptStatus.ACTIVE, nullable=False
    )
    is_duplicate_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    collected_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    cancel_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    imported_from: Mapped[str | None] = mapped_column(String(256), nullable=True)

    items: Mapped[list["ReceiptItem"]] = relationship(
        "ReceiptItem", back_populates="receipt", order_by="ReceiptItem.sort_order"
    )
    payments: Mapped[list["ReceiptPayment"]] = relationship(
        "ReceiptPayment", back_populates="receipt"
    )
    corrections: Mapped[list["ReceiptCorrection"]] = relationship(
        "ReceiptCorrection", back_populates="receipt"
    )
    student: Mapped["Student | None"] = relationship("Student")
    collector: Mapped["User"] = relationship("User", foreign_keys=[collected_by])


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("receipts.id"), nullable=False)
    fee_head_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fee_heads.id"), nullable=True)
    fee_head_name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="items")
    fee_head: Mapped["FeeHead | None"] = relationship("FeeHead")


class ReceiptPayment(Base):
    __tablename__ = "receipt_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("receipts.id"), nullable=False)
    payment_mode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("payment_modes.id"), nullable=True
    )
    payment_mode_name: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    branch_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cheque_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cheque_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dd_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dd_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    upi_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), default=PaymentStatus.CLEARED, nullable=False
    )
    clearance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bounce_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="payments")
    payment_mode: Mapped["PaymentMode | None"] = relationship("PaymentMode")


class ReceiptCorrection(Base):
    __tablename__ = "receipt_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(Integer, ForeignKey("receipts.id"), nullable=False)
    corrected_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="corrections")
    corrected_by_user: Mapped["User"] = relationship("User", foreign_keys=[corrected_by])


from app.models.student import Student  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
from app.models.fee import FeeHead  # noqa: E402, F401
from app.models.org import PaymentMode  # noqa: E402, F401
