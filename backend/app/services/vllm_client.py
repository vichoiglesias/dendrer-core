"""
vLLM client for communicating with vLLM inference server.
"""
import httpx
from typing import Any

from app.config import get_settings
from app.schemas.inference import ChatMessage

settings = get_settings()


class VLLMError(Exception):
    """Raised when vLLM request fails."""
    pass


class VLLMClient:
    """Client for vLLM inference server."""

    def __init__(self, endpoint: str | None = None):
        """
        Initialize vLLM client.

        Args:
            endpoint: vLLM server endpoint (defaults to config value)
        """
        self.endpoint = endpoint or settings.vllm_endpoint
        self.timeout = 60.0  # 60 second timeout

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float = 1.0,
        stop: list[str] | str | None = None,
    ) -> dict[str, Any]:
        """
        Make a chat completion request to vLLM.

        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stop: Stop sequences

        Returns:
            vLLM response dictionary

        Raises:
            VLLMError: If request fails
        """
        # Convert messages to vLLM format
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": temperature,
            "top_p": top_p,
        }

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        if stop is not None:
            payload["stop"] = stop if isinstance(stop, list) else [stop]

        # Make request to vLLM server
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.endpoint}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            raise VLLMError("Request to vLLM server timed out")
        except httpx.HTTPStatusError as e:
            raise VLLMError(f"vLLM server returned error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise VLLMError(f"Failed to connect to vLLM server: {str(e)}")
        except Exception as e:
            raise VLLMError(f"Unexpected error: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if vLLM server is healthy.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.endpoint}/health")
                return response.status_code == 200
        except Exception:
            return False
