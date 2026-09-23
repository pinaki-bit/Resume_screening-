"""
backend/app/api/dependencies.py

FastAPI dependency functions for authentication and role-based access control.

Security enhancements (v0.3.0):
  - JWT token is checked against the TokenBlocklist (revoked tokens rejected).
  - Users with must_change_password=True are blocked from all endpoints
    except /api/v1/auth/change-password and /api/v1/auth/me.
  - Token JTI is extracted and passed through for revocation support.

Design principles:
  - Authorization is ALWAYS enforced server-side — never rely on frontend visibility.
  - Every protected endpoint declares its required role via Depends().
  - Token validation is strict: expired, malformed, or missing tokens all return 401.
  - Role mismatches return 403 (authenticated but not authorized).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User
from app.models.token_blocklist import TokenBlocklist

# Bearer token extractor (auto_error=False so we can return a clean 401)
_bearer = HTTPBearer(auto_error=False)

# Endpoints that are exempt from the force-password-change guard.
# Users with must_change_password=True can only access these paths.
_PASSWORD_CHANGE_EXEMPT_PATHS = {
    "/api/v1/auth/change-password",
    "/api/v1/auth/me",
    "/api/v1/auth/logout",
}


def _extract_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ],
) -> str:
    """Extract the raw JWT string from the Authorization header."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_user(
    request: Request,
    token: Annotated[str, Depends(_extract_token)],
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT, check the blocklist, and return the matching User.

    Security checks (in order):
      1. Token is valid and not expired.
      2. Token JTI is NOT in the blocklist (revoked tokens rejected).
      3. User exists and is active.
      4. If must_change_password is True, only password-change endpoints allowed.

    Raises HTTP 401 for invalid/expired/revoked tokens.
    Raises HTTP 403 for disabled accounts or force-password-change.
    """
    # --- Step 1: Decode and validate token ---
    try:
        payload = decode_access_token(token)
        email: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if not email:
            raise ValueError("No subject in token")
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Step 2: Check token blocklist ---
    if jti:
        blocked = (
            db.query(TokenBlocklist.id)
            .filter(TokenBlocklist.jti == jti)
            .first()
        )
        if blocked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # --- Step 3: Validate user ---
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact an administrator.",
        )

    # --- Step 4: Force password change guard ---
    if user.must_change_password:
        request_path = request.url.path.rstrip("/")
        if request_path not in _PASSWORD_CHANGE_EXEMPT_PATHS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Password change required. Your account is using default "
                    "credentials. Please change your password at "
                    "POST /api/v1/auth/change-password before accessing other endpoints."
                ),
            )

    return user


# ---------------------------------------------------------------------------
# Role-specific dependencies
# ---------------------------------------------------------------------------

CurrentUser = Annotated[User, Depends(get_current_user)]


def _require_role(*allowed_roles: str):
    """
    Factory that returns a FastAPI dependency function requiring one of the
    given roles. Usage:

        @router.get("/admin/stuff")
        def admin_stuff(user: User = Depends(require_admin)):
            ...
    """
    def _dep(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"This action requires one of these roles: "
                    f"{', '.join(allowed_roles)}. "
                    f"Your role is '{current_user.role}'."
                ),
            )
        return current_user
    return _dep


require_admin = _require_role("admin")
require_hr_or_admin = _require_role("admin", "hr")
require_any_role = _require_role("admin", "hr", "readonly")


# ---------------------------------------------------------------------------
# Annotated shorthands for cleaner route signatures
# ---------------------------------------------------------------------------

AdminUser = Annotated[User, Depends(require_admin)]
HRUser = Annotated[User, Depends(require_hr_or_admin)]
AnyAuthUser = Annotated[User, Depends(require_any_role)]
