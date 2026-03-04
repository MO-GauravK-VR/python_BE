from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# --- Request Schemas ---

class UserSignUpRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


# --- Response Schemas ---

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SignUpResponse(BaseModel):
    message: str
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class ProfileResponse(BaseModel):
    message: str
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str  # In production, send this via email instead


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
