from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from .common import BaseSchema


class DepartmentBase(BaseModel):
    name: str
    type: str = "TEACHING"
    description: str | None = None
    nch_code: str | None = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(BaseSchema, DepartmentBase):
    id: int


class DesignationBase(BaseModel):
    name: str
    department_id: int | None = None
    category: str | None = None
    is_teaching: bool = False
    min_wage_category: str | None = None
    is_active: bool = True


class DesignationCreate(DesignationBase):
    pass


class DesignationOut(BaseSchema, DesignationBase):
    id: int


class BankDetailIn(BaseModel):
    account_number: str
    ifsc: str
    bank_name: str
    branch: str | None = None
    is_primary: bool = True


class BankDetailOut(BaseSchema):
    id: int
    account_masked: str
    ifsc: str
    bank_name: str
    branch: str | None
    is_primary: bool


class EmployeeBase(BaseModel):
    emp_code: str
    first_name: str
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    dob: date | None = None
    gender: str | None = None
    marital_status: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    spouse_name: str | None = None
    address: str | None = None
    state: str | None = None
    department_id: int | None = None
    designation_id: int | None = None
    date_of_joining: date | None = None
    date_of_exit: date | None = None
    employment_type: str = "PERMANENT"
    is_active: bool = True
    epf_applicable: bool = True
    esi_applicable: bool = True
    pt_applicable: bool = True
    lwf_applicable: bool = True
    tds_applicable: bool = True
    city_tier: str = "NON_METRO"
    state_for_pt: str | None = None


class EmployeeCreate(EmployeeBase):
    pan: str | None = None
    aadhaar: str | None = None
    uan: str | None = None
    esi_ip_number: str | None = None
    bank_details: list[BankDetailIn] | None = None


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    department_id: int | None = None
    designation_id: int | None = None
    date_of_exit: date | None = None
    is_active: bool | None = None
    epf_applicable: bool | None = None
    esi_applicable: bool | None = None
    pt_applicable: bool | None = None
    lwf_applicable: bool | None = None
    tds_applicable: bool | None = None
    pan: str | None = None
    aadhaar: str | None = None
    uan: str | None = None
    esi_ip_number: str | None = None


class EmployeeOut(BaseSchema, EmployeeBase):
    id: int
    pan_masked: str | None = None
    aadhaar_masked: str | None = None
    uan: str | None = None
    esi_ip_number: str | None = None
    bank_details: list[BankDetailOut] = []
    created_at: datetime
