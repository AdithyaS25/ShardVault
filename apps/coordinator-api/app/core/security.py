"""
core/security.py — ShardLock Coordinator API
=============================================
Password hashing and JWT token utilities.

FIX APPLIED:
  - Removed duplicate create_access_token() definition.
    The first definition (with fixed 15-min expiry) was being silently
    overwritten by the second. Merged into one clean function that
    accepts an optional expires_delta.
"""

import secrets
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password Hashing ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# app/core/security.py
import bcrypt

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data          : Payload dict — must include {"sub": user_id_str}
        expires_delta : Optional custom expiry. Defaults to
                        settings.ACCESS_TOKEN_EXPIRE_MINUTES (15 min).
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ── Refresh Token ─────────────────────────────────────────────────────────────

def create_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token string."""
    return secrets.token_urlsafe(64)