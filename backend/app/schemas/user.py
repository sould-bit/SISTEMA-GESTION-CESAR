from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(min_length=6)
    role_id: UUID

    @validator("username")
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError("Username must be alphanumeric (dots, underscores, hyphens allowed)")
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    branch_id: Optional[int] = None
    role_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)

class UserRead(UserBase):
    id: int
    company_id: int
    role_id: Optional[UUID] = None
    role_name: Optional[str] = None
    # Include role details if needed, but for list simplistic is fine. 
    # Can extend later.
    
    class Config:
        from_attributes = True
