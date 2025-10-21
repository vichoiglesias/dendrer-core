"""
Subscription model for user billing and plan management.
"""
from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import String, ForeignKey, DateTime, Enum as SQLEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class PlanTier(str, enum.Enum):
    """Subscription plan tiers."""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


class Subscription(Base, TimestampMixin):
    """User subscription and billing information."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # User reference
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Plan details
    plan: Mapped[PlanTier] = mapped_column(
        SQLEnum(PlanTier, name="plan_tier"),
        nullable=False,
        default=PlanTier.FREE,
    )

    # Subscription status
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus, name="subscription_status"),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
    )

    # Stripe integration
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    # Billing period
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Usage tracking (current billing period)
    tokens_used_this_period: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Trial information
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"plan={self.plan}, status={self.status})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    @property
    def quota_limit(self) -> int:
        """Get token quota limit for current plan."""
        from app.config import get_settings
        settings = get_settings()

        quota_map = {
            PlanTier.FREE: settings.free_tier_quota,
            PlanTier.PRO: settings.pro_tier_quota,
            PlanTier.BUSINESS: settings.business_tier_quota,
            PlanTier.ENTERPRISE: 999_999_999,  # Unlimited for enterprise
        }
        return quota_map.get(self.plan, settings.free_tier_quota)

    @property
    def quota_remaining(self) -> int:
        """Get remaining token quota for current period."""
        return max(0, self.quota_limit - self.tokens_used_this_period)

    @property
    def quota_usage_percent(self) -> float:
        """Get quota usage as percentage."""
        if self.quota_limit == 0:
            return 0.0
        return (self.tokens_used_this_period / self.quota_limit) * 100
