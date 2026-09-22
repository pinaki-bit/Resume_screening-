"""
backend/app/services/audit_service.py

Audit logging service.

Rules:
  - Audit events are written synchronously before the response returns.
  - Events must NEVER contain resume text, passwords, tokens, or complete PII.
  - Failed writes are logged to the application log (not silently ignored).
  - Events are append-only — no update or delete operations on audit records.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


def log_event(
    db: Session,
    *,
    event_type: str,
    summary: str,
    actor_id: int | None = None,
    actor_email: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    outcome: str = "success",
) -> AuditEvent | None:
    """
    Write an audit event to the database.

    Args:
        db:            Active SQLAlchemy session.
        event_type:    Dot-notation category (e.g. "auth.login", "resume.download").
        summary:       Short human-readable description. NO PII or secrets.
        actor_id:      User ID (None for unauthenticated events).
        actor_email:   Email for denormalized lookup (never a password).
        resource_type: Type of resource affected (e.g. "resume", "job").
        resource_id:   Public ID of the resource.
        detail:        Structured context dict. Must NOT contain sensitive content.
        ip_address:    Request IP address.
        user_agent:    Request User-Agent header.
        outcome:       "success" | "failure" | "error"

    Returns:
        The created AuditEvent, or None if the write failed.
    """
    detail_json = None
    if detail:
        try:
            detail_json = json.dumps(detail, default=str)
        except (TypeError, ValueError):
            detail_json = json.dumps({"note": "detail serialization failed"})

    try:
        event = AuditEvent(
            actor_id=actor_id,
            actor_email=actor_email,
            event_type=event_type,
            summary=summary,
            detail_json=detail_json,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            outcome=outcome,
        )
        db.add(event)
        db.commit()
        return event
    except Exception as exc:
        # Never let audit failures break the main request — log and continue.
        logger.error("Failed to write audit event '%s': %s", event_type, exc)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def log_auth_event(
    db: Session,
    *,
    success: bool,
    actor_email: str,
    actor_id: int | None = None,
    ip_address: str | None = None,
) -> None:
    """Convenience wrapper for authentication events."""
    log_event(
        db,
        event_type="auth.login" if success else "auth.login_failed",
        summary=(
            f"Successful login for {actor_email}"
            if success
            else f"Failed login attempt for {actor_email}"
        ),
        actor_id=actor_id,
        actor_email=actor_email,
        ip_address=ip_address,
        outcome="success" if success else "failure",
    )


def log_resume_access(
    db: Session,
    *,
    actor_id: int,
    actor_email: str,
    resume_public_id: str,
    action: str,  # "view" | "download" | "process"
    ip_address: str | None = None,
) -> None:
    """Convenience wrapper for resume access events."""
    log_event(
        db,
        event_type=f"resume.{action}",
        summary=f"Resume {action} by {actor_email}",
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type="resume",
        resource_id=resume_public_id,
        ip_address=ip_address,
        outcome="success",
    )
