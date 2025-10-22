"""
Inference request tracking for usage monitoring and billing.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.model import Model


class InferenceRequest(Base, TimestampMixin):
    """Track inference requests for monitoring and billing."""

    __tablename__ = "inference_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User who made the request
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Model used for inference
    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Model name (denormalized for historical tracking if model is deleted)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Request details
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Performance metrics
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)  # Response time in milliseconds

    # Request metadata (optional)
    request_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Error tracking (if request failed)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Success flag
    success: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    model: Mapped["Model | None"] = relationship("Model", back_populates="inference_requests")

    def __repr__(self) -> str:
        return (
            f"<InferenceRequest(id={self.id}, user_id={self.user_id}, "
            f"model='{self.model_name}', tokens={self.total_tokens})>"
        )
