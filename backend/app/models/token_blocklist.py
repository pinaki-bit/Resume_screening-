"""
backend/app/models/token_blocklist.py

Stores revoked JWT token IDs (JTIs) for server-side token invalidation.

When a user logs out or an admin revokes tokens, the token's JTI is
inserted here. On every authenticated request, the JTI is checked
against this table — if found, the request is rejected with 401.

Cleanup:
  - Expired entries (expires_at < now) can be safely purged via a
    scheduled task or admin endpoint. They are kept temporarily for
    audit completeness.
"""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # JWT ID — the unique identifier embedded in every token
    jti: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Which user's token was revoked
    user_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # When the token was blocked
    blocked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # When the original token would have expired (for cleanup)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Why the token was revoked
    reason: Mapped[str] = mapped_column(
        String(128), nullable=False, default="logout"
    )
    # "logout" | "password_change" | "admin_revoke" | "account_disabled"

    def __repr__(self) -> str:
        return (
            f"<TokenBlocklist jti={self.jti[:8]}… "
            f"user={self.user_email!r} reason={self.reason!r}>"
        )
