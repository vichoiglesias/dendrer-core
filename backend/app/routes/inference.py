"""
OpenAI-compatible inference endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.inference import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse
from app.services.inference import InferenceService, InferenceError
from app.services.usage import QuotaExceededError, UsageService
from app.utils.database import get_db
from app.utils.dependencies import CurrentUserFromAPIKey

router = APIRouter()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    current_user: CurrentUserFromAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a chat completion (OpenAI-compatible).

    This endpoint is compatible with OpenAI's chat completions API.
    Use your API key in the Authorization header:
    `Authorization: Bearer sk_live_...`

    Requires API key authentication.
    Tracks usage and enforces quota limits based on subscription plan.
    """
    # Check for streaming (not supported yet)
    if request.stream:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Streaming is not supported yet"
        )

    # Check for multiple completions (not supported yet)
    if request.n != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only n=1 is supported"
        )

    # Create inference service
    inference_service = InferenceService()

    try:
        # Process chat completion
        response = await inference_service.chat_completion(
            db=db,
            user=current_user,
            request=request,
        )

        return response

    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "message": str(e),
                    "type": "quota_exceeded",
                    "code": "insufficient_quota"
                }
            }
        )

    except InferenceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": str(e),
                    "type": "inference_error",
                    "code": "inference_failed"
                }
            }
        )

    except Exception as e:
        # Log unexpected errors (in production, use proper logging)
        print(f"Unexpected error in chat completion: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "An unexpected error occurred",
                    "type": "internal_error",
                    "code": "internal_server_error"
                }
            }
        )


@router.get("/usage")
async def get_usage_stats(
    current_user: CurrentUserFromAPIKey,
    db: AsyncSession = Depends(get_db),
):
    """
    Get usage statistics for the current user.

    Returns token usage, quota limits, and request counts.

    Requires API key authentication.
    """
    stats = await UsageService.get_user_usage_stats(db, current_user.id)
    return stats
