"""
API Key management service.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import APIKey, User
from app.schemas.api_key import APIKeyCreate
from app.utils.security import generate_api_key, get_api_key_prefix, verify_api_key


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    async def create_api_key(
        db: AsyncSession,
        user_id: int,
        key_data: APIKeyCreate
    ) -> tuple[APIKey, str]:
        """
        Create a new API key for a user.

        Args:
            db: Database session
            user_id: ID of the user
            key_data: API key creation data

        Returns:
            Tuple of (APIKey model, raw_key)
            The raw_key should be shown to the user only once!
        """
        # Generate API key
        raw_key, key_hash = generate_api_key()
        key_prefix = get_api_key_prefix(raw_key)

        # Create API key record
        api_key = APIKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_data.name,
            is_active=True,
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        return api_key, raw_key

    @staticmethod
    async def get_user_api_keys(
        db: AsyncSession,
        user_id: int
    ) -> list[APIKey]:
        """
        Get all API keys for a user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            List of API keys
        """
        result = await db.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_api_key(
        db: AsyncSession,
        user_id: int,
        key_id: int
    ) -> bool:
        """
        Delete (revoke) an API key.

        Args:
            db: Database session
            user_id: ID of the user (for authorization)
            key_id: ID of the API key to delete

        Returns:
            True if deleted, False if not found or unauthorized
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return False

        await db.delete(api_key)
        await db.commit()
        return True

    @staticmethod
    async def verify_api_key(
        db: AsyncSession,
        raw_key: str
    ) -> User | None:
        """
        Verify an API key and return the associated user.

        Args:
            db: Database session
            raw_key: Raw API key from request

        Returns:
            User if key is valid, None otherwise
        """
        # Get key prefix for faster lookup
        key_prefix = get_api_key_prefix(raw_key)

        # Find API key by prefix
        result = await db.execute(
            select(APIKey).where(APIKey.key_prefix == key_prefix)
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        # Verify the full key
        if not verify_api_key(raw_key, api_key.key_hash):
            return None

        # Check if key is valid (active and not expired)
        if not api_key.is_valid:
            return None

        # Update last_used_at
        api_key.last_used_at = datetime.utcnow()
        await db.commit()

        # Get and return the user
        result = await db.execute(
            select(User).where(User.id == api_key.user_id)
        )
        user = result.scalar_one_or_none()

        return user
