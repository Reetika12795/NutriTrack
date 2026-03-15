"""Pydantic schemas for user and auth endpoints."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    age_group: str | None = None
    activity_level: str | None = None
    dietary_goal: str | None = None
    consent_data_processing: bool = False


class UserOut(BaseModel):
    user_id: uuid.UUID
    email: str
    username: str
    role: str
    age_group: str | None = None
    activity_level: str | None = None
    dietary_goal: str | None = None
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str
