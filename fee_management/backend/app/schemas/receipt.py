"""Receipt and related schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class FinancialYearCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_active: bool = False
    is_locked: bool = False


class FinancialYearOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    start_date: date
    end_date: date
    is_active: bool
    is_locked: bool
    next_receipt_number: int
    created_at: datetime


class PaymentModeCreate(BaseModel):
    name: str
    code: str
    is_active: bool = True
    sort_order: int = 0
    requires_reference: bool = False
    requires_bank_name: bool = False
    requires_date: bool = False
    description: Optional[str] = None


class PaymentModeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    is_active: bool
    sort_order: int
    requires_reference: bool
    requires_bank_name: bool
    requires_date: bool
    description: Optional[str] = None


class ReceiptItemIn(BaseModel):
    fee_head_id: Optional[int] = None
    fee_head_name: str
    amount: Decimal
    sort_order: int = 0


class ReceiptItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fee_head_id: Optional[int] = None
    fee_head_name: str
    amount: Decimal
    sort_order: int


class ReceiptPaymentIn(BaseModel):
    payment_mode_id: Optional[int] = None
    payment_mode_name: str
    amount: Decimal
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    dd_number: Optional[str] = None
    dd_date: Optional[date] = None
    upi_id: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_date: Optional[date] = None
    payment_status: str = "CLEARED"
    remarks: Optional[str] = None


class ReceiptPaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_mode_id: Optional[int] = None
    payment_mode_name: str
    amount: Decimal
    reference_number: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None
    dd_number: Optional[str] = None
    dd_date: Optional[date] = None
    upi_id: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_date: Optional[date] = None
    payment_status: str
    clearance_date: Optional[date] = None
    bounce_reason: Optional[str] = None
    remarks: Optional[str] = None


class ReceiptCreate(BaseModel):
    student_id: Optional[int] = None
    financial_year_id: int
    receipt_date: date
    items: List[ReceiptItemIn]
    payments: List[ReceiptPaymentIn]
    remarks: Optional[str] = None
    # Manual overrides for denormalised fields (e.g. for manual receipts)
    student_name: Optional[str] = None
    father_name: Optional[str] = None
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    session_name: Optional[str] = None
    professional_year: Optional[int] = None
    roll_number: Optional[str] = None
    admission_number: Optional[str] = None


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    receipt_number: str
    financial_year_id: int
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    father_name: Optional[str] = None
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    session_name: Optional[str] = None
    professional_year: Optional[int] = None
    roll_number: Optional[str] = None
    admission_number: Optional[str] = None
    receipt_date: date
    total_amount: Decimal
    amount_in_words: Optional[str] = None
    remarks: Optional[str] = None
    status: str
    is_duplicate_print: bool
    collected_by: int
    created_at: datetime
    updated_at: datetime
    cancel_reason: Optional[str] = None
    cancel_at: Optional[datetime] = None
    imported_from: Optional[str] = None
    items: List[ReceiptItemOut] = []
    payments: List[ReceiptPaymentOut] = []
    fy_name: Optional[str] = None
    collector_name: Optional[str] = None


class ReceiptCancelRequest(BaseModel):
    reason: str


class ReceiptCorrection(BaseModel):
    reason: str
    remarks: Optional[str] = None
    items: Optional[List[ReceiptItemIn]] = None
    payments: Optional[List[ReceiptPaymentIn]] = None


class BulkUploadSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_name: str
    uploaded_by: int
    uploaded_at: datetime
    financial_year_id: Optional[int] = None
    total_rows: int
    success_rows: int
    failed_rows: int
    duplicate_rows: int
    status: str
    rollback_at: Optional[datetime] = None
    notes: Optional[str] = None


class BulkUploadRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    row_number: int
    raw_data: Optional[Dict[str, Any]] = None
    parsed_data: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    receipt_id: Optional[int] = None
