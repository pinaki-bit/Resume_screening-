"""
backend/app/services/email_service.py

Mock email service for sending secure notifications (e.g. system health, security alerts).
In a production environment, this would integrate with SendGrid, SES, or Mailgun.
"""

import logging
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory mock inbox for testing
_MOCK_INBOX = []


class EmailNotification:
    def __init__(self, to_email: str, subject: str, body: str, is_secure: bool = True):
        self.to_email = to_email
        self.subject = subject
        self.body = body
        self.is_secure = is_secure
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "to": self.to_email,
            "subject": self.subject,
            "body": self.body,
            "secure": self.is_secure,
            "timestamp": self.timestamp
        }


def send_security_alert(user_email: str, event_type: str, details: str) -> bool:
    """Send a high-priority security alert."""
    subject = f"SECURITY ALERT: {event_type}"
    body = f"A security event was detected on your account.\n\nDetails: {details}\n\nIf you did not authorize this, contact your administrator immediately."
    
    notification = EmailNotification(user_email, subject, body, is_secure=True)
    _mock_send(notification)
    return True


def send_system_health_report(admin_email: str, metrics: dict) -> bool:
    """Send a daily or weekly system health report."""
    subject = "System Health Report"
    body = f"Current System Telemetry:\n\n{json.dumps(metrics, indent=2)}"
    
    notification = EmailNotification(admin_email, subject, body, is_secure=True)
    _mock_send(notification)
    return True


def _mock_send(notification: EmailNotification) -> None:
    """Mock sending the email by logging it and storing it in memory."""
    _MOCK_INBOX.append(notification)
    logger.info("MOCK EMAIL SENT to %s: [%s]", notification.to_email, notification.subject)
    
    # Optionally write to a local log file for verification
    log_path = Path("email_logs.json")
    try:
        if log_path.exists():
            logs = json.loads(log_path.read_text())
        else:
            logs = []
        logs.append(notification.to_dict())
        log_path.write_text(json.dumps(logs, indent=2))
    except Exception as exc:
        logger.warning("Could not write email log: %s", exc)


def get_mock_inbox() -> list[dict]:
    """Retrieve all sent mock emails (useful for testing)."""
    return [msg.to_dict() for msg in _MOCK_INBOX]
