"""
backend/app/models/job.py

Job description and requirement ORM models.
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, Float, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.screening import ScreeningResult


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Non-guessable public identifier used in API URLs
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Who created this job (FK to users.id)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

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
    requirements: Mapped[list["JobRequirement"]] = relationship(
        "JobRequirement", back_populates="job",
        cascade="all, delete-orphan", lazy="selectin"
    )
    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        "ScreeningResult", back_populates="job", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r}>"


class JobRequirement(Base):
    """
    Individual skill/requirement for a job.
    Required skills have a higher weight than preferred skills.
    """
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Relative weight within the required/preferred group (default 1.0)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    job: Mapped["Job"] = relationship("Job", back_populates="requirements")

    def __repr__(self) -> str:
        label = "required" if self.is_required else "preferred"
        return f"<JobRequirement {self.skill_name!r} [{label}] w={self.weight}>"
