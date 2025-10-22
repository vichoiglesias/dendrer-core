"""
Security utilities for password hashing and JWT tokens.
"""
import secrets
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"sub": user_id})
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload, or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    """
    Generate a secure API key.

    Returns:
        Tuple of (raw_key, key_hash) where:
        - raw_key: The key to give to the user (show only once)
        - key_hash: The hashed key to store in database
    """
    # Generate a secure random key
    raw_key = f"sk_live_{secrets.token_urlsafe(32)}"

    # Hash the key for storage
    key_hash = hash_password(raw_key)

    return raw_key, key_hash


def get_api_key_prefix(api_key: str) -> str:
    """
    Extract the prefix from an API key for identification.

    Args:
        api_key: Full API key

    Returns:
        Key prefix (e.g., "sk_live_abc")
    """
    # Return first 15 characters as prefix
    return api_key[:15] if len(api_key) >= 15 else api_key


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash.

    Args:
        plain_key: Plain API key from request
        hashed_key: Hashed key from database

    Returns:
        True if key matches, False otherwise
    """
    return verify_password(plain_key, hashed_key)
