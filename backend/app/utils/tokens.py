"""
Token counting utilities for billing and quota management.
"""
from typing import Any

from app.schemas.inference import ChatMessage


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.

    This is a simple estimation based on character count.
    For production, you should use the actual tokenizer for your model.

    Rule of thumb: ~4 characters per token for English text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Simple estimation: 1 token ≈ 4 characters
    return max(1, len(text) // 4)


def count_message_tokens(message: ChatMessage) -> int:
    """
    Count tokens in a single chat message.

    Args:
        message: Chat message

    Returns:
        Token count
    """
    # Count tokens in content
    content_tokens = estimate_tokens(message.content)

    # Add overhead for role formatting (approximately 4 tokens per message)
    # This accounts for special tokens like <|im_start|>, role name, etc.
    overhead = 4

    return content_tokens + overhead


def count_messages_tokens(messages: list[ChatMessage]) -> int:
    """
    Count tokens in a list of chat messages.

    Args:
        messages: List of chat messages

    Returns:
        Total token count
    """
    total = sum(count_message_tokens(msg) for msg in messages)

    # Add overhead for the conversation structure
    # This accounts for the final assistant turn prompt
    total += 3

    return total


def extract_tokens_from_vllm_response(response: dict[str, Any]) -> tuple[int, int, int]:
    """
    Extract token counts from vLLM response.

    Args:
        response: vLLM response dictionary

    Returns:
        Tuple of (prompt_tokens, completion_tokens, total_tokens)
    """
    usage = response.get("usage", {})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    # Fallback: if vLLM doesn't provide usage, estimate from response
    if total_tokens == 0:
        # Try to estimate from the response content
        choices = response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            completion_tokens = estimate_tokens(content)

    return prompt_tokens, completion_tokens, total_tokens


# For future: Use actual tokenizer
# This would be more accurate but adds dependency on transformers
#
# from transformers import AutoTokenizer
#
# class TokenCounter:
#     def __init__(self, model_name: str):
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#
#     def count_tokens(self, text: str) -> int:
#         return len(self.tokenizer.encode(text))
