"""
backend/app/core/security.py

JWT creation / verification and password hashing utilities.

Dependencies:
    python-jose[cryptography]  — JWT
    bcrypt>=4.0.1              — password hashing (direct, avoids passlib 1.7.4 compat issue)
"""

from __future__ import annotations

import datetime
from typing import Any

import bcrypt
from jose import jwt

from app.config import get_settings

# ---------------------------------------------------------------------------
# Password hashing  (direct bcrypt — avoids passlib/bcrypt 4.x mismatch)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain* text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str | Any,
    expires_delta: datetime.timedelta | None = None,
) -> tuple[str, int]:
    """
    Create a signed JWT.

    Returns:
        (encoded_token, expires_in_seconds)
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        )

    expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        jose.JWTError — if the token is invalid or expired.
    """
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    return payload
