"""
backend/app/models/skill.py

ExtractedSkill ORM model.

Stores individual skills extracted from a resume by the NLP pipeline.
One resume has many extracted skills.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.resume import Resume


class ExtractedSkill(Base):
    __tablename__ = "extracted_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resume_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Canonical skill name from the taxonomy (e.g. "scikit-learn")
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # Exact text that was matched in the resume
    matched_text: Mapped[str] = mapped_column(String(256), nullable=False)
    # Domain this skill belongs to (e.g. "Data Science")
    domain: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Skill category within domain (e.g. "ml_frameworks")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Evidence snippet (surrounding text, without full resume dump)
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    # How the skill was found (e.g. "phrase_matcher", "exact_match")
    extraction_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="phrase_matcher"
    )
    # Number of occurrences in the resume
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    extracted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationship
    resume: Mapped["Resume"] = relationship("Resume", back_populates="extracted_skills")

    def __repr__(self) -> str:
        return (
            f"<ExtractedSkill {self.canonical_name!r} "
            f"resume_id={self.resume_id} freq={self.frequency}>"
        )
