"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.database import get_db
from app.utils.security import decode_access_token
from app.services.api_key import APIKeyService

# HTTP Bearer token scheme for Swagger UI
security = HTTPBearer()


async def get_current_user_from_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.

    Extracts JWT token from Authorization header and returns the user.

    Args:
        credentials: HTTP Bearer token
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_user_from_api_key(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from API key.

    Extracts API key from Authorization header and returns the user.
    Expected format: "Bearer sk_live_..."

    Args:
        authorization: Authorization header value
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If API key is invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract API key from "Bearer <key>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = parts[1]

    # Verify API key and get user
    user = await APIKeyService.verify_api_key(db, api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user_from_jwt)]
CurrentUserFromAPIKey = Annotated[User, Depends(get_current_user_from_api_key)]
