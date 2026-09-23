"""
backend/app/core/security.py

JWT creation / verification, password hashing, and token revocation utilities.

Security enhancements (v0.3.0):
  - Every JWT now contains a unique `jti` (JWT ID) claim for revocation support.
  - Tokens include `iat` (issued-at) for audit trail.
  - `decode_access_token` returns the full payload including `jti`.
  - Password hashing uses direct bcrypt (avoids passlib 1.7.4 compat issue).

Dependencies:
    python-jose[cryptography]  — JWT
    bcrypt>=4.0.1              — password hashing (direct, avoids passlib 1.7.4 compat issue)
"""

from __future__ import annotations

import datetime
import uuid
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
) -> tuple[str, int, str]:
    """
    Create a signed JWT with a unique JTI for revocation support.

    Returns:
        (encoded_token, expires_in_seconds, jti)
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    expire = now + expires_delta
    jti = uuid.uuid4().hex

    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, int(expires_delta.total_seconds()), jti


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Returns:
        The full payload dict including 'sub', 'exp', 'iat', 'jti'.

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


def extract_jti(token: str) -> str | None:
    """
    Extract the JTI from a JWT without full validation.
    Used when we need the JTI even for potentially expired tokens (e.g., logout).

    Returns None if the token is malformed.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False},  # Allow expired tokens for revocation
        )
        return payload.get("jti")
    except Exception:
        return None
