"""
backend/app/schemas/user.py

Pydantic v2 schemas for authentication and user management.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    is_admin: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: str = "hr"


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
