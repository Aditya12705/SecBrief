"""API key authentication for SecBrief."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from db import create_api_key, get_api_key_by_email, get_api_key_by_key


def generate_api_key(email: str) -> str:
    """Generate and store a new API key for an email."""
    key = f"sk_live_{secrets.token_urlsafe(32)}"
    create_api_key(email, key)
    return key


def validate_api_key(api_key: str) -> str:
    """Validate API key and return associated email."""
    key_data = get_api_key_by_key(api_key)
    if not key_data or key_data.get("is_active") != 1:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return key_data["email"]


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> str:
    """FastAPI dependency to get current user from Bearer token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    api_key = authorization[7:]
    return validate_api_key(api_key)
