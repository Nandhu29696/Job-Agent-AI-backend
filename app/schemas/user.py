from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = Field(None, max_length=255)


class RegisterRequest(BaseModel):
    """Public registration. Deliberately has no `role` field."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str

    @field_validator("password")
    @classmethod
    def strong(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=128)


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=10, pattern=r"^\d+$")


class ResetPasswordRequest(VerifyOtpRequest):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong(cls, v: str) -> str:
        return validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str | None = Field(None, max_length=128)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    avatar_url: str | None = Field(None, max_length=500)


class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool = True
    auth_provider: str = "local"
    avatar_url: str | None = None
    plan: str = "free"
    plan_expires_at: datetime | None = None
    is_pro: bool = False
    has_password: bool = True
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(Token):
    user: UserOut


class MessageResponse(BaseModel):
    message: str
    code: str | None = None
