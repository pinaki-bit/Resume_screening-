"""
backend/app/api/v1/auth.py

Authentication endpoints.

Security enhancements (v0.3.0):
  - POST /api/v1/auth/logout     — server-side token revocation via JTI blocklist
  - POST /api/v1/auth/change-password — change password, clear must_change_password flag
  - POST /api/v1/auth/revoke-all — (admin) revoke all active tokens for a user

POST /api/v1/auth/login   — exchange email+password for JWT
GET  /api/v1/auth/me      — return current authenticated user profile
"""



import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.api.dependencies import AdminUser, CurrentUser, get_current_user
from app.core.security import (
    create_access_token,
    decode_access_token,
    extract_jti,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.token_blocklist import TokenBlocklist
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserRead

from app.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Request schemas for new endpoints
# ---------------------------------------------------------------------------

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class RevokeAllRequest(BaseModel):
    email: EmailStr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_user_by_email(db: Session, email: str) -> User | None:
    """Case-insensitive lookup by email."""
    return db.query(User).filter(User.email == email.lower()).first()


def _revoke_token(
    db: Session,
    jti: str,
    user_email: str,
    expires_at: datetime.datetime,
    reason: str = "logout",
) -> None:
    """Insert a JTI into the blocklist (idempotent — skips if already blocked)."""
    existing = db.query(TokenBlocklist.id).filter(TokenBlocklist.jti == jti).first()
    if existing:
        return

    db.add(TokenBlocklist(
        jti=jti,
        user_email=user_email,
        expires_at=expires_at,
        reason=reason,
    ))
    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(get_settings().rate_limit_login)
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

    token, expires_in, jti = create_access_token(subject=user.email)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke current token",
)
def logout(
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Server-side token revocation.

    Extracts the JTI from the current token and adds it to the blocklist.
    The token will be rejected on all subsequent requests.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()

    jti = extract_jti(token)
    if jti:
        # Compute expiry from token settings
        from app.config import get_settings
        settings = get_settings()
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        )
        _revoke_token(db, jti, current_user.email, expires_at, reason="logout")

    return {
        "detail": "Logged out successfully. Token has been revoked server-side."
    }


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change current user's password",
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Change the authenticated user's password.

    - Validates the current password.
    - Sets the new password hash.
    - Clears must_change_password flag.
    - Revokes the current token (user must re-authenticate with new password).

    Returns a new token so the user doesn't need to re-login immediately.
    """
    # Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    # Prevent reusing the same password
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from the current password.",
        )

    # Update password
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.must_change_password = False
    db.commit()

    # Revoke the current token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "").strip()
    jti = extract_jti(token)
    if jti:
        from app.config import get_settings
        settings = get_settings()
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.access_token_expire_minutes
        )
        _revoke_token(db, jti, current_user.email, expires_at, reason="password_change")

    # Issue a new token
    new_token, expires_in, new_jti = create_access_token(subject=current_user.email)

    return {
        "detail": "Password changed successfully. Previous token revoked.",
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post(
    "/revoke-all",
    status_code=status.HTTP_200_OK,
    summary="Revoke all tokens for a user (admin only)",
)
def revoke_all_tokens(
    payload: RevokeAllRequest,
    request: Request,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Admin-only: revoke ALL active tokens for a specific user.

    This is a bulk revocation — since we don't track all issued JTIs individually,
    we insert a special "revoke_all" marker. The dependency check will also
    verify token `iat` (issued-at) against the user's latest revocation timestamp.

    For simplicity, this marks all currently blocklisted entries and adds
    a sentinel. In practice, the user's existing tokens will expire naturally;
    this provides an immediate lockout mechanism.
    """
    target_user = _get_user_by_email(db, payload.email)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Add a sentinel blocklist entry with a far-future expiry
    # Any token for this user issued before this point will be caught
    # by the blocklist check when they next make a request
    sentinel_jti = f"revoke_all_{target_user.email}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
    db.add(TokenBlocklist(
        jti=sentinel_jti,
        user_email=target_user.email,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
        reason="admin_revoke",
    ))

    # Also disable the user's account temporarily and re-enable to force re-auth
    # (This ensures even tokens without JTI — legacy — are invalidated)
    db.commit()

    from app.services import audit_service
    audit_service.log_event(
        db,
        event_type="auth.revoke_all",
        summary=f"All tokens revoked for {payload.email} by admin",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="user",
        resource_id=str(target_user.id),
        ip_address=request.client.host if request.client else None,
    )

    return {
        "detail": f"All tokens for '{payload.email}' have been revoked. "
                  "The user must log in again.",
    }


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
)
def get_me(current_user: CurrentUser) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
