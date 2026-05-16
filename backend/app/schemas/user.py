from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from .common import BaseSchema


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None
    password: str = Field(min_length=8)
    role: str = "auditor"


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserOut(BaseSchema):
    id: int
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    force_password_change: bool
    last_login: datetime | None
    created_at: datetime
