"""
Model registry for managing LLM models.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.inference_request import InferenceRequest


class ModelStatus(str, enum.Enum):
    """Model deployment status."""
    PENDING = "pending"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class Model(Base, TimestampMixin):
    """Model registry for LLM models."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Model identification
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Model source (e.g., "huggingface", "custom")
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="huggingface")

    # HuggingFace model ID or S3 path
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Model configuration (quantization, context length, etc.)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Deployment status
    status: Mapped[ModelStatus] = mapped_column(
        SQLEnum(ModelStatus, name="model_status"),
        nullable=False,
        default=ModelStatus.PENDING,
    )

    # Pricing (tokens per dollar, or fixed cost)
    # This will be used for billing calculations
    tokens_per_dollar: Mapped[int | None] = mapped_column(nullable=True)

    # Model capabilities
    supports_chat: Mapped[bool] = mapped_column(default=True, nullable=False)
    supports_completion: Mapped[bool] = mapped_column(default=True, nullable=False)
    supports_embeddings: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Model metadata
    context_length: Mapped[int] = mapped_column(default=4096, nullable=False)
    max_tokens: Mapped[int] = mapped_column(default=2048, nullable=False)

    # Relationships
    inference_requests: Mapped[list["InferenceRequest"]] = relationship(
        "InferenceRequest",
        back_populates="model",
    )

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name='{self.name}', status={self.status})>"
