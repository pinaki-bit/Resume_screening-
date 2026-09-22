"""
backend/app/models/candidate.py

Candidate ORM model.

A Candidate represents a person applying for a position.
One candidate may have multiple resumes (e.g. revised versions).
The candidate record stores anonymised reference information only.
"""

from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.screening import ScreeningResult


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True,
        default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Optional contact details — stored only if explicitly provided by HR
    # Never inferred from resume text
    reference_code: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    resumes: Mapped[list["Resume"]] = relationship(
        "Resume", back_populates="candidate", lazy="selectin"
    )
    screening_results: Mapped[list["ScreeningResult"]] = relationship(
        "ScreeningResult", back_populates="candidate", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} ref={self.reference_code!r}>"
