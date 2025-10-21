"""
Usage tracking service for inference requests and quota management.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InferenceRequest, User, Subscription, Model


class QuotaExceededError(Exception):
    """Raised when user exceeds their quota."""
    pass


class UsageService:
    """Service for tracking usage and enforcing quotas."""

    @staticmethod
    async def check_quota(db: AsyncSession, user: User) -> tuple[bool, int, int]:
        """
        Check if user has remaining quota.

        Args:
            db: Database session
            user: User to check quota for

        Returns:
            Tuple of (has_quota, used_tokens, quota_limit)

        Raises:
            QuotaExceededError: If user has exceeded their quota
        """
        # Get user's subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise QuotaExceededError("No active subscription found")

        # Check if subscription is active
        if not subscription.is_active:
            raise QuotaExceededError("Subscription is not active")

        # Get quota limit and usage
        quota_limit = subscription.quota_limit
        tokens_used = subscription.tokens_used_this_period

        # Check if quota exceeded
        has_quota = tokens_used < quota_limit

        return has_quota, tokens_used, quota_limit

    @staticmethod
    async def track_inference_request(
        db: AsyncSession,
        user_id: int,
        model_id: int | None,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: int,
        success: bool = True,
        error_code: str | None = None,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> InferenceRequest:
        """
        Track an inference request for billing and analytics.

        Args:
            db: Database session
            user_id: User ID
            model_id: Model ID (can be None)
            model_name: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens used
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded
            error_code: Error code if failed
            error_message: Error message if failed
            metadata: Optional metadata

        Returns:
            Created inference request record
        """
        # Create inference request record
        inference_request = InferenceRequest(
            user_id=user_id,
            model_id=model_id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=success,
            error_code=error_code,
            error_message=error_message,
            request_metadata=metadata,
        )

        db.add(inference_request)

        # Update subscription usage (only for successful requests)
        if success and total_tokens > 0:
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.tokens_used_this_period += total_tokens

        await db.commit()
        await db.refresh(inference_request)

        return inference_request

    @staticmethod
    async def get_user_usage_stats(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """
        Get usage statistics for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Dictionary with usage statistics
        """
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return {
                "tokens_used": 0,
                "quota_limit": 0,
                "quota_remaining": 0,
                "quota_usage_percent": 0,
            }

        # Get total requests count
        result = await db.execute(
            select(func.count(InferenceRequest.id))
            .where(InferenceRequest.user_id == user_id)
        )
        total_requests = result.scalar() or 0

        # Get successful requests count
        result = await db.execute(
            select(func.count(InferenceRequest.id))
            .where(
                InferenceRequest.user_id == user_id,
                InferenceRequest.success == True
            )
        )
        successful_requests = result.scalar() or 0

        return {
            "tokens_used": subscription.tokens_used_this_period,
            "quota_limit": subscription.quota_limit,
            "quota_remaining": subscription.quota_remaining,
            "quota_usage_percent": subscription.quota_usage_percent,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "plan": subscription.plan.value,
            "status": subscription.status.value,
        }
