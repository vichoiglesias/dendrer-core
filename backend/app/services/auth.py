"""
Authentication service for user registration and login.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Subscription, PlanTier, SubscriptionStatus
from app.schemas.auth import UserRegister, UserLogin
from app.utils.security import hash_password, verify_password, create_access_token


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    async def register_user(
        db: AsyncSession,
        user_data: UserRegister
    ) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data

        Returns:
            Created user

        Raises:
            AuthenticationError: If email already exists
        """
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise AuthenticationError("Email already registered")

        # Create new user
        hashed_password = hash_password(user_data.password)

        new_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            company=user_data.company,
            is_active=True,
            is_superuser=False,
            email_verified=False,
        )

        db.add(new_user)
        await db.flush()  # Flush to get user.id

        # Create free tier subscription for new user
        subscription = Subscription(
            user_id=new_user.id,
            plan=PlanTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow(),
            tokens_used_this_period=0,
        )

        db.add(subscription)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        credentials: UserLogin
    ) -> User:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            credentials: User login credentials

        Returns:
            Authenticated user

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("Invalid email or password")

        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        return user

    @staticmethod
    def create_user_token(user: User) -> str:
        """
        Create JWT token for a user.

        Args:
            user: User to create token for

        Returns:
            JWT access token
        """
        token_data = {
            "sub": str(user.id),
            "email": user.email,
        }

        return create_access_token(token_data)
