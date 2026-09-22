"""
backend/app/models/screening.py

ScreeningResult ORM model.

One ScreeningResult links a Resume to a Job and stores:
  - skill-match percentage (transparent formula)
  - required / preferred skill coverage
  - matched and missing skills
  - classification result reference
  - overall relevance score (weighted composite)
  - human review status
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.resume import Resume
    from app.models.candidate import Candidate


class ReviewStatus:
    """Enum-like constants for human review status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"

    ALL = {PENDING, APPROVED, REJECTED, ON_HOLD}


class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )

    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    candidate_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # ── Skill match scores (0.0 – 100.0) ──────────────────────────────────
    required_skill_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_skill_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    combined_skill_match: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Skills matched/missing (stored as JSON string for SQLite compat) ──
    # Format: JSON array of canonical skill names
    matched_required_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_required_skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_preferred_skills: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Classification ────────────────────────────────────────────────────
    predicted_domain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prediction_confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )

    # ── Overall relevance score (composite, 0.0 – 100.0) ─────────────────
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # JSON string describing how the score was computed (for explainability)
    score_breakdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Weights configuration snapshot used for this result
    scoring_weights: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Human review ──────────────────────────────────────────────────────
    review_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReviewStatus.PENDING, index=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    screened_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="screening_results")
    job: Mapped["Job"] = relationship("Job", back_populates="screening_results")
    candidate: Mapped["Candidate | None"] = relationship(
        "Candidate", back_populates="screening_results"
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningResult id={self.id} "
            f"resume={self.resume_id} job={self.job_id} "
            f"score={self.relevance_score} review={self.review_status!r}>"
        )
