from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    salary_expectation: Optional[int] = None
    auto_apply: Optional[bool] = None
    experience_level: Optional[str] = None
    apify_api_token: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    full_name: Optional[str]
    preferred_roles: Optional[List[str]]
    preferred_locations: Optional[List[str]]
    salary_expectation: Optional[int]
    experience_level: Optional[str] = None
    apify_api_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
