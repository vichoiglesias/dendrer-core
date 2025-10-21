"""
Authentication endpoints for user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth import AuthService, AuthenticationError
from app.utils.database import get_db
from app.utils.dependencies import CurrentUser

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Creates a new user with a free tier subscription.
    """
    try:
        user = await AuthService.register_user(db, user_data)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.

    Returns a JWT access token for authenticated requests.
    """
    try:
        user = await AuthService.authenticate_user(db, credentials)
        access_token = AuthService.create_user_token(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user
