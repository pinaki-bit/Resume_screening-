"""
backend/app/schemas/resume.py

Pydantic v2 schemas for Resume upload and processing results.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class ResumeRead(BaseModel):
    id: int
    public_id: str
    candidate_id: int | None
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    status: str
    error_message: str | None
    text_char_count: int | None
    predicted_domain: str | None
    prediction_confidence: str | None
    uploaded_at: datetime.datetime
    processed_at: datetime.datetime | None

    # extracted_text is intentionally EXCLUDED from API responses
    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Returned immediately after a successful upload (before processing)."""
    public_id: str
    status: str
    message: str


class ExtractedSkillRead(BaseModel):
    id: int
    canonical_name: str
    matched_text: str
    domain: str | None
    category: str | None
    evidence_snippet: str | None
    extraction_method: str
    frequency: int

    model_config = {"from_attributes": True}


class ResumeDetailRead(ResumeRead):
    """Full resume detail including extracted skills."""
    extracted_skills: list[ExtractedSkillRead] = []
