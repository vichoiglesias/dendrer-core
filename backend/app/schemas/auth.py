"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str | None = Field(None, max_length=255, description="User full name")
    company: str | None = Field(None, max_length=255, description="Company name")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    email: str
    is_active: bool
    is_superuser: bool
    email_verified: bool
    full_name: str | None
    company: str | None
    created_at: str

    class Config:
        from_attributes = True
