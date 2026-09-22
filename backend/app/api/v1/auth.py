"""
backend/app/api/v1/auth.py

Authentication endpoints.

POST /api/v1/auth/login   — exchange email+password for JWT
POST /api/v1/auth/logout  — client-side token invalidation (stateless JWT note)
GET  /api/v1/auth/me      — return current authenticated user profile
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import CurrentUser, get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _get_user_by_email(db: Session, email: str) -> User | None:
    """Case-insensitive lookup by email."""
    return db.query(User).filter(User.email == email.lower()).first()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.

    Security notes:
    - Uses constant-time password comparison path whether or not the user exists.
    - Returns a generic error message for both wrong email and wrong password
      to prevent user enumeration.
    - Audit logging is handled by the audit service (Phase 6).
    """
    user = _get_user_by_email(db, payload.email)

    # Constant-time path: always call verify_password even when user is None
    # to prevent timing-based user enumeration.
    # The dummy hash is a valid bcrypt hash of the string "dummy_sentinel_value".
    # It is never a real credential — it only ensures the bcrypt work factor
    # is always paid regardless of whether the user exists.
    _DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/BxAO1f6nZsEYUL.Aa"
    password_ok = False
    try:
        password_ok = verify_password(
            payload.password,
            user.hashed_password if user else _DUMMY_HASH,
        )
    except ValueError:
        # bcrypt raises ValueError for malformed hashes — treat as mismatch
        password_ok = False

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )

    token, expires_in = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout (client-side token discard)",
)
def logout(current_user: CurrentUser) -> dict:
    """
    Stateless JWT logout.

    Because JWTs are stateless, the server cannot invalidate them. The client
    MUST discard the token from memory. If token revocation is required,
    implement a server-side blocklist (future enhancement).
    """
    return {
        "detail": "Logged out successfully. Discard your token on the client."
    }


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
def get_me(current_user: CurrentUser) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
