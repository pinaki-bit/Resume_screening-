"""
backend/app/models/resume.py

Resume ORM model.

Stores upload metadata and processing status.
The actual PDF is stored on disk (not in the DB) under a server-generated UUID filename.
Resume text is stored in the DB for NLP/ML processing but must NEVER appear in logs.
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.skill import ExtractedSkill
    from app.models.screening import ScreeningResult


class ProcessingStatus:
    """Enum-like constants for resume processing status."""
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"

    ALL = {UPLOADED, QUEUED, PROCESSING, COMPLETED, NEEDS_REVIEW, FAILED}


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )

    candidate_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Original filename as submitted (for UI display only — never used for storage)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # Internal storage filename (UUID-based, no path traversal possible)
    stored_filename: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="application/pdf")
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProcessingStatus.UPLOADED, index=True
    )
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Extracted text (never logged, redacted in error responses)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ML classification result
    predicted_domain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prediction_confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)  # e.g. "high", "medium", "low"
    model_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )

    uploaded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    candidate: Mapped["Candidate | None"] = relationship(
        "Candidate", back_populates="resumes"
    )
    extracted_skills: Mapped[list["ExtractedSkill"]] = relationship(
        "ExtractedSkill", back_populates="resume",
        cascade="all, delete-orphan", lazy="selectin"
    )
    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        "ScreeningResult", back_populates="resume", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return (
            f"<Resume id={self.id} status={self.status!r} "
            f"domain={self.predicted_domain!r}>"
        )
