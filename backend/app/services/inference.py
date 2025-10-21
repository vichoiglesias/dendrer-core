"""
Main inference service orchestrating chat completions.
"""
import time
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Model, ModelStatus
from app.schemas.inference import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
)
from app.services.vllm_client import VLLMClient, VLLMError
from app.services.usage import UsageService, QuotaExceededError
from app.utils.tokens import count_messages_tokens, extract_tokens_from_vllm_response


class InferenceError(Exception):
    """Raised when inference fails."""
    pass


class InferenceService:
    """Service for handling inference requests."""

    def __init__(self):
        self.vllm_client = VLLMClient()

    async def chat_completion(
        self,
        db: AsyncSession,
        user: User,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """
        Process a chat completion request.

        Args:
            db: Database session
            user: Authenticated user
            request: Chat completion request

        Returns:
            Chat completion response

        Raises:
            QuotaExceededError: If user exceeds quota
            InferenceError: If inference fails
        """
        start_time = time.time()

        # Get model from database
        model = await self._get_model(db, request.model)

        # Check user quota BEFORE making inference
        try:
            has_quota, tokens_used, quota_limit = await UsageService.check_quota(db, user)

            if not has_quota:
                raise QuotaExceededError(
                    f"Quota exceeded. Used {tokens_used}/{quota_limit} tokens. "
                    f"Please upgrade your plan or wait for quota reset."
                )
        except QuotaExceededError:
            # Track failed request due to quota
            latency_ms = int((time.time() - start_time) * 1000)
            await UsageService.track_inference_request(
                db=db,
                user_id=user.id,
                model_id=model.id if model else None,
                model_name=request.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_code="quota_exceeded",
                error_message="Insufficient quota"
            )
            raise

        # Make inference request to vLLM
        try:
            vllm_response = await self.vllm_client.chat_completion(
                messages=request.messages,
                model=model.model_path if model else request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop,
            )
        except VLLMError as e:
            # Track failed request
            latency_ms = int((time.time() - start_time) * 1000)
            await UsageService.track_inference_request(
                db=db,
                user_id=user.id,
                model_id=model.id if model else None,
                model_name=request.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                latency_ms=latency_ms,
                success=False,
                error_code="vllm_error",
                error_message=str(e)
            )
            raise InferenceError(f"Inference failed: {str(e)}")

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Extract token counts from vLLM response
        prompt_tokens, completion_tokens, total_tokens = extract_tokens_from_vllm_response(vllm_response)

        # Fallback: estimate if vLLM doesn't provide counts
        if prompt_tokens == 0:
            prompt_tokens = count_messages_tokens(request.messages)

        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        # Track successful inference request
        await UsageService.track_inference_request(
            db=db,
            user_id=user.id,
            model_id=model.id if model else None,
            model_name=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            success=True,
        )

        # Convert vLLM response to our format
        response = self._convert_vllm_response(
            vllm_response=vllm_response,
            model_name=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        return response

    async def _get_model(self, db: AsyncSession, model_name: str) -> Model | None:
        """
        Get model from database.

        Args:
            db: Database session
            model_name: Model name or identifier

        Returns:
            Model if found, None otherwise

        Raises:
            InferenceError: If model not found or not ready
        """
        result = await db.execute(
            select(Model).where(Model.name == model_name)
        )
        model = result.scalar_one_or_none()

        if not model:
            # For MVP, allow requests even if model not in DB
            # In production, you'd want to enforce this
            return None

        if model.status != ModelStatus.READY:
            raise InferenceError(f"Model '{model_name}' is not ready. Status: {model.status}")

        return model

    def _convert_vllm_response(
        self,
        vllm_response: dict,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> ChatCompletionResponse:
        """
        Convert vLLM response to OpenAI-compatible format.

        Args:
            vllm_response: Raw vLLM response
            model_name: Model name
            prompt_tokens: Prompt token count
            completion_tokens: Completion token count
            total_tokens: Total token count

        Returns:
            ChatCompletionResponse
        """
        # Extract choices from vLLM response
        vllm_choices = vllm_response.get("choices", [])

        choices = []
        for idx, choice in enumerate(vllm_choices):
            message_data = choice.get("message", {})
            message = ChatMessage(
                role=message_data.get("role", "assistant"),
                content=message_data.get("content", "")
            )

            finish_reason = choice.get("finish_reason", "stop")
            # Map vLLM finish reasons to our format
            if finish_reason not in ["stop", "length", "error"]:
                finish_reason = "stop"

            choices.append(
                ChatCompletionChoice(
                    index=idx,
                    message=message,
                    finish_reason=finish_reason,
                )
            )

        # Generate unique ID
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

        # Create response
        response = ChatCompletionResponse(
            id=completion_id,
            object="chat.completion",
            created=int(datetime.utcnow().timestamp()),
            model=model_name,
            choices=choices,
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ),
        )

        return response
