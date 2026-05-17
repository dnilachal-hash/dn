"""Report-related schemas."""
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    today_collection: Decimal
    month_collection: Decimal
    fy_collection: Decimal
    today_receipt_count: int
    month_receipt_count: int
    fy_receipt_count: int
    collection_by_mode: Dict[str, Decimal]
    pending_cheques: int
    bounced_cheques: int
    cancelled_receipts_today: int
    recent_receipts: List[Dict[str, Any]] = []
    active_students: int
    total_students: int


class CollectionReport(BaseModel):
    date: Optional[date] = None
    month: Optional[int] = None
    year: Optional[int] = None
    total_amount: Decimal
    receipt_count: int
    by_fee_head: List[Dict[str, Any]] = []
    by_payment_mode: List[Dict[str, Any]] = []
    receipts: List[Dict[str, Any]] = []


class DueReport(BaseModel):
    student_id: int
    admission_number: str
    student_name: str
    father_name: Optional[str] = None
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    professional_year: Optional[int] = None
    total_fees: Decimal
    total_paid: Decimal
    balance: Decimal
    fee_head_dues: List[Dict[str, Any]] = []


class StudentFeeReport(BaseModel):
    student_id: int
    student_name: str
    admission_number: str
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    receipts: List[Dict[str, Any]] = []
    total_paid: Decimal
    total_assigned: Decimal
    balance: Decimal
    by_fee_head: List[Dict[str, Any]] = []
