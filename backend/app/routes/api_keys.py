"""
API Key management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreated
from app.services.api_key import APIKeyService
from app.utils.database import get_db
from app.utils.dependencies import CurrentUser

router = APIRouter()


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key.

    The full API key is returned only once. Store it securely!

    Requires JWT authentication.
    """
    api_key, raw_key = await APIKeyService.create_api_key(
        db,
        current_user.id,
        key_data
    )

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,  # Full key shown only once!
        key_prefix=api_key.key_prefix,
        created_at=api_key.created_at,
    )


@router.get("", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys for the current user.

    Requires JWT authentication.
    """
    api_keys = await APIKeyService.get_user_api_keys(db, current_user.id)
    return api_keys


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (revoke) an API key.

    Requires JWT authentication.
    """
    deleted = await APIKeyService.delete_api_key(db, current_user.id, key_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    return None
