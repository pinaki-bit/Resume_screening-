"""
backend/app/models/user.py

User ORM model with role-based access control.

Roles:
  admin    — full system access
  hr       — create jobs, upload/view resumes, review candidates
  readonly — view authorized job and candidate information only
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit_event import AuditEvent
    from app.models.notification import Notification


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Role: "admin" | "hr" | "readonly"
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="hr", index=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Kept for backward compat — role=="admin" is the authoritative check
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        "AuditEvent", back_populates="actor", lazy="dynamic"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="recipient", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
