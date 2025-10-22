"""
Pydantic schemas for API keys.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""

    name: str | None = Field(None, max_length=255, description="Optional name for the key")


class APIKeyResponse(BaseModel):
    """Schema for API key response."""

    id: int
    name: str | None
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyCreated(BaseModel):
    """Schema for newly created API key (includes full key)."""

    id: int
    name: str | None
    key: str = Field(..., description="Full API key (shown only once!)")
    key_prefix: str
    created_at: datetime

    class Config:
        from_attributes = True
