"""Receipt, bulk upload, and correction models."""
import enum
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Date, Text, Numeric, JSON,
    Enum as SAEnum, ForeignKey,
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
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    BOUNCED = "BOUNCED"
    CANCELLED = "CANCELLED"


class BulkUploadStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class BulkRowStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"
    SKIPPED = "SKIPPED"


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    financial_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=False, index=True
    )
    student_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("students.id"), nullable=True, index=True
    )
    # Denormalised fields for historical integrity
    student_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    father_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    course_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    batch_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    session_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    professional_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    roll_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    admission_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    receipt_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_in_words: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ReceiptStatus] = mapped_column(
        SAEnum(ReceiptStatus, name="receiptstatus"),
        default=ReceiptStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    is_duplicate_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    collected_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancel_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    cancel_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    imported_from: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    financial_year: Mapped["app.models.org.FinancialYear"] = relationship("FinancialYear")
    student: Mapped[Optional["app.models.student.Student"]] = relationship("Student")
    collector: Mapped["app.models.user.User"] = relationship(
        "User", foreign_keys=[collected_by]
    )
    canceller: Mapped[Optional["app.models.user.User"]] = relationship(
        "User", foreign_keys=[cancel_by]
    )
    items: Mapped[list["ReceiptItem"]] = relationship(
        "ReceiptItem", back_populates="receipt", cascade="all, delete-orphan"
    )
    payments: Mapped[list["ReceiptPayment"]] = relationship(
        "ReceiptPayment", back_populates="receipt", cascade="all, delete-orphan"
    )
    corrections: Mapped[list["ReceiptCorrection"]] = relationship(
        "ReceiptCorrection", back_populates="receipt", cascade="all, delete-orphan"
    )


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fee_head_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fee_heads.id"), nullable=True
    )
    fee_head_name: Mapped[str] = mapped_column(String(256), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="items")
    fee_head: Mapped[Optional["app.models.fee.FeeHead"]] = relationship("FeeHead")


class ReceiptPayment(Base):
    __tablename__ = "receipt_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_mode_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("payment_modes.id"), nullable=True
    )
    payment_mode_name: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    cheque_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cheque_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dd_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dd_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    upi_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    transaction_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="paymentstatus"),
        default=PaymentStatus.CLEARED,
        nullable=False,
    )
    clearance_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="payments")
    payment_mode: Mapped[Optional["app.models.org.PaymentMode"]] = relationship("PaymentMode")


class ReceiptCorrection(Base):
    __tablename__ = "receipt_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    corrected_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    corrected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    receipt: Mapped["Receipt"] = relationship("Receipt", back_populates="corrections")
    corrector: Mapped["app.models.user.User"] = relationship("User")


class BulkUploadSession(Base):
    __tablename__ = "bulk_upload_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(256), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    financial_year_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("financial_years.id"), nullable=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[BulkUploadStatus] = mapped_column(
        SAEnum(BulkUploadStatus, name="bulkuploadstatus"),
        default=BulkUploadStatus.PENDING,
        nullable=False,
    )
    rollback_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rollback_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    uploader: Mapped["app.models.user.User"] = relationship(
        "User", foreign_keys=[uploaded_by]
    )
    rollback_user: Mapped[Optional["app.models.user.User"]] = relationship(
        "User", foreign_keys=[rollback_by]
    )
    financial_year: Mapped[Optional["app.models.org.FinancialYear"]] = relationship("FinancialYear")
    rows: Mapped[list["BulkUploadRow"]] = relationship(
        "BulkUploadRow", back_populates="session", cascade="all, delete-orphan"
    )


class BulkUploadRow(Base):
    __tablename__ = "bulk_upload_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bulk_upload_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[BulkRowStatus] = mapped_column(
        SAEnum(BulkRowStatus, name="bulkrowstatus"),
        default=BulkRowStatus.SKIPPED,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("receipts.id"), nullable=True
    )

    session: Mapped["BulkUploadSession"] = relationship("BulkUploadSession", back_populates="rows")
    receipt: Mapped[Optional["Receipt"]] = relationship("Receipt")
