"""
backend/app/models/__init__.py

Import every ORM model here so SQLAlchemy's metadata registry is complete
before create_all() or Alembic runs.
"""

from app.models.user import User  # noqa: F401
from app.models.job import Job, JobRequirement  # noqa: F401
from app.models.candidate import Candidate  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.skill import ExtractedSkill  # noqa: F401
from app.models.screening import ScreeningResult  # noqa: F401
from app.models.model_version import ModelVersion  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.audit_event import AuditEvent  # noqa: F401

__all__ = [
    "User",
    "Job",
    "JobRequirement",
    "Candidate",
    "Resume",
    "ExtractedSkill",
    "ScreeningResult",
    "ModelVersion",
    "Notification",
    "AuditEvent",
]
