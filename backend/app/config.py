"""
Application configuration using Pydantic Settings.
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Dendrer"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://dendrer:dendrer@localhost:5432/dendrer"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Inference
    vllm_endpoint: str = "http://localhost:8001"
    default_model: str = "mistralai/Mistral-7B-Instruct-v0.3"

    # Quotas (tokens per month)
    free_tier_quota: int = 10_000
    pro_tier_quota: int = 1_000_000
    business_tier_quota: int = 5_000_000


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
