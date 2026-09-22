"""
backend/app/models/notification.py

Notification ORM model.

Stores email notification records for delivery tracking and audit purposes.
Never stores complete resume content, passwords, or tokens.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    recipient_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    # Template name used (not full body — full body never stored)
    template_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # Serialized context keys (NOT values containing sensitive data)
    context_keys: Mapped[str | None] = mapped_column(Text, nullable=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    send_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship
    recipient: Mapped["User | None"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} to={self.recipient_email!r} "
            f"event={self.event_type!r} sent={self.is_sent}>"
        )
