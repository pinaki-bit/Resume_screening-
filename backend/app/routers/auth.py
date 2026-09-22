"""
backend/app/routers/auth.py

Authentication endpoints.

POST /auth/login  — exchange email+password for a JWT access token
GET  /auth/me     — return the currently authenticated user (Phase 3+)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a User by email (case-insensitive)."""
    return db.query(User).filter(User.email == email.lower()).first()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    status_code=status.HTTP_200_OK,
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate with email + password.

    Returns a JWT bearer token that must be sent in the `Authorization`
    header for protected endpoints:

        Authorization: Bearer <token>

    Raises HTTP 401 if credentials are invalid.
    """
    user = _get_user_by_email(db, payload.email)

    # Use a constant-time comparison to prevent timing attacks even when the
    # user is not found.
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )

    token, expires_in = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, expires_in=expires_in)
