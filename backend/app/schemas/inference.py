"""
OpenAI-compatible inference schemas for chat completions.
"""
from typing import Literal, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["system", "user", "assistant"] = Field(
        ..., description="The role of the message author"
    )
    content: str = Field(..., description="The content of the message")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str = Field(..., description="ID of the model to use")
    messages: list[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(default=None, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop: list[str] | str | None = Field(default=None, description="Stop sequences")
    stream: bool = Field(default=False, description="Stream the response")
    n: int = Field(default=1, ge=1, le=1, description="Number of completions (only 1 supported for now)")
    user: str | None = Field(default=None, description="User identifier for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "mistral-7b-instruct",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello! How are you?"}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        }


class ChatCompletionUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used")


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int = Field(..., description="The index of this choice")
    message: ChatMessage = Field(..., description="The generated message")
    finish_reason: Literal["stop", "length", "error"] = Field(
        ..., description="Why the completion finished"
    )


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str = Field(..., description="Unique identifier for this completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used for completion")
    choices: list[ChatCompletionChoice] = Field(..., description="List of completion choices")
    usage: ChatCompletionUsage = Field(..., description="Token usage information")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chatcmpl-abc123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "mistral-7b-instruct",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 15,
                    "total_tokens": 35
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response for failed requests."""

    error: dict[str, Any] = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "message": "Insufficient quota. Please upgrade your plan.",
                    "type": "quota_exceeded",
                    "code": "insufficient_quota"
                }
            }
        }
