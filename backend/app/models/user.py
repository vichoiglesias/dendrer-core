"""
User model for authentication and account management.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.subscription import Subscription


class User(Base, TimestampMixin):
    """User model for account management."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Optional profile fields
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"
