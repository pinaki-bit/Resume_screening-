"""
backend/app/models/audit_event.py

AuditEvent ORM model.

Every security-sensitive action is recorded here:
  - Authentication (login, logout, failure)
  - Permission changes
  - Resume access / download / export
  - Job configuration changes
  - Model deployment events
  - Administrative actions

Rules:
  - Audit events are immutable once created.
  - Resume content, passwords, tokens, and PII MUST NOT appear in detail fields.
  - Actor may be null for unauthenticated events (e.g. failed login attempts).
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Who performed the action (null = unauthenticated request)
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Action category (e.g. "auth.login", "resume.download", "admin.role_change")
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Human-readable summary
    summary: Mapped[str] = mapped_column(String(512), nullable=False)
    # Extra structured data as JSON string (no sensitive content)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resource involved (optional)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Network context
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Outcome
    outcome: Mapped[str] = mapped_column(
        String(32), nullable=False, default="success", index=True
    )  # "success" | "failure" | "error"

    occurred_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationship
    actor: Mapped["User | None"] = relationship("User", back_populates="audit_events")

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id} type={self.event_type!r} "
            f"actor={self.actor_email!r} outcome={self.outcome!r}>"
        )
