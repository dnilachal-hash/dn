"""Fee-related schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class FeeHeadCreate(BaseModel):
    name: str
    code: str
    fee_type: str = "OTHER"
    is_refundable: bool = False
    frequency: str = "YEARLY"
    is_compulsory: bool = True
    is_active: bool = True
    description: Optional[str] = None
    sort_order: int = 0


class FeeHeadUpdate(BaseModel):
    name: Optional[str] = None
    fee_type: Optional[str] = None
    is_refundable: Optional[bool] = None
    frequency: Optional[str] = None
    is_compulsory: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class FeeHeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    fee_type: str
    is_refundable: bool
    frequency: str
    is_compulsory: bool
    is_active: bool
    description: Optional[str] = None
    sort_order: int
    created_at: datetime


class FeeStructureItemIn(BaseModel):
    fee_head_id: int
    amount: Decimal
    is_compulsory: bool = True
    sort_order: int = 0


class FeeStructureItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fee_head_id: int
    fee_head_name: Optional[str] = None
    amount: Decimal
    is_compulsory: bool
    sort_order: int


class FeeStructureCreate(BaseModel):
    name: str
    course_id: int
    batch_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    financial_year_id: int
    is_active: bool = True
    items: List[FeeStructureItemIn] = []


class FeeStructureUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    is_frozen: Optional[bool] = None
    items: Optional[List[FeeStructureItemIn]] = None


class FeeStructureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    course_id: int
    batch_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    financial_year_id: int
    is_active: bool
    is_frozen: bool
    created_at: datetime
    items: List[FeeStructureItemOut] = []
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    fy_name: Optional[str] = None
    total_amount: Optional[Decimal] = None


class StudentFeeOverrideCreate(BaseModel):
    student_id: int
    fee_head_id: int
    financial_year_id: int
    override_amount: Decimal
    reason: Optional[str] = None


class StudentFeeOverrideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    fee_head_id: int
    financial_year_id: int
    override_amount: Decimal
    reason: Optional[str] = None
    created_at: datetime
