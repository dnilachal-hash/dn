"""Student and academic structure schemas."""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    code: str
    duration_years: int
    is_active: bool
    description: Optional[str] = None
    created_at: datetime


class CourseCreate(BaseModel):
    name: str
    code: str
    duration_years: int = 5
    is_active: bool = True
    description: Optional[str] = None


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    name: str
    start_year: int
    end_year: int
    is_active: bool
    created_at: datetime


class BatchCreate(BaseModel):
    course_id: int
    name: str
    start_year: int
    end_year: int
    is_active: bool = True


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime


class SessionCreate(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = False


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class StudentCreate(BaseModel):
    admission_number: str
    student_name: str
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    category_id: Optional[int] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin: Optional[str] = None
    course_id: Optional[int] = None
    batch_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    professional_year: Optional[int] = None
    semester: Optional[int] = None
    roll_number: Optional[str] = None
    registration_number: Optional[str] = None
    enrollment_number: Optional[str] = None
    admission_date: Optional[date] = None
    student_status: str = "ACTIVE"
    is_hostel: bool = False
    is_transport: bool = False
    scholarship_status: Optional[str] = None
    remarks: Optional[str] = None


class StudentUpdate(BaseModel):
    student_name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    category_id: Optional[int] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin: Optional[str] = None
    course_id: Optional[int] = None
    batch_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    professional_year: Optional[int] = None
    semester: Optional[int] = None
    roll_number: Optional[str] = None
    registration_number: Optional[str] = None
    enrollment_number: Optional[str] = None
    admission_date: Optional[date] = None
    student_status: Optional[str] = None
    is_hostel: Optional[bool] = None
    is_transport: Optional[bool] = None
    scholarship_status: Optional[str] = None
    remarks: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admission_number: str
    student_name: str
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    guardian_name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    category_id: Optional[int] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin: Optional[str] = None
    course_id: Optional[int] = None
    batch_id: Optional[int] = None
    academic_session_id: Optional[int] = None
    professional_year: Optional[int] = None
    semester: Optional[int] = None
    roll_number: Optional[str] = None
    registration_number: Optional[str] = None
    enrollment_number: Optional[str] = None
    admission_date: Optional[date] = None
    student_status: str
    is_hostel: bool
    is_transport: bool
    scholarship_status: Optional[str] = None
    remarks: Optional[str] = None
    photo_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Resolved names from relationships
    course_name: Optional[str] = None
    batch_name: Optional[str] = None
    session_name: Optional[str] = None
    category_name: Optional[str] = None


class StudentListOut(BaseModel):
    items: List[StudentOut]
    total: int
    page: int
    page_size: int
    pages: int
