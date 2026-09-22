"""
backend/app/api/v1/resumes.py

Resume upload and management endpoints.

POST /api/v1/resumes/upload
    - Validates file (extension, magic bytes, size)
    - Stores under UUID filename
    - Runs full processing pipeline synchronously:
        1. PDF text extraction
        2. NLP skill extraction
        3. ML domain classification
    - Persists Resume + ExtractedSkill records
    - Returns processing result

GET  /api/v1/resumes
    - List all resumes (hr, admin) or own uploads (readonly)
GET  /api/v1/resumes/{resume_id}
    - Resume detail with extracted skills

DELETE /api/v1/resumes/{resume_id}
    - Admin-only soft delete (mark as failed/archived)
"""

from __future__ import annotations

import datetime
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminUser, AnyAuthUser, HRUser
from app.database import get_db
from app.models.candidate import Candidate
from app.models.resume import Resume, ProcessingStatus
from app.models.skill import ExtractedSkill
from app.schemas.resume import ResumeDetailRead, ResumeRead, ResumeUploadResponse
from app.services import audit_service
from app.services import pdf_service
from app.services.pdf_service import PDFValidationError
from app.services import skill_service
from app.services import classification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resumes", tags=["Resumes"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_resume_or_404(db: Session, resume_id: str) -> Resume:
    resume = db.query(Resume).filter(Resume.public_id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return resume


def _run_processing_pipeline(
    resume: Resume,
    file_path: str,
    db: Session,
) -> None:
    """
    Run the full processing pipeline on an uploaded PDF.

    Steps:
      1. Extract text from PDF
      2. Extract skills via NLP PhraseMatcher
      3. Classify domain with ML model
      4. Persist results

    This function updates the Resume record in-place.
    Must be called within an active DB transaction.
    """
    resume.status = ProcessingStatus.PROCESSING

    # --- Step 1: Extract text ---
    extraction = pdf_service.extract_text_from_path(file_path)

    if not extraction.success:
        resume.status = ProcessingStatus.FAILED
        resume.error_message = extraction.error
        resume.page_count = extraction.page_count
        resume.processed_at = datetime.datetime.now(datetime.timezone.utc)
        logger.warning(
            "PDF extraction failed for resume %s: %s",
            resume.public_id, extraction.error
        )
        return

    resume.extracted_text = extraction.text
    resume.text_char_count = extraction.char_count
    resume.page_count = extraction.page_count

    # --- Step 2: Skill extraction ---
    matched_skills = skill_service.match_skills(extraction.text)

    skill_objects = [
        ExtractedSkill(
            resume_id=resume.id,
            canonical_name=m.canonical_name,
            matched_text=m.matched_text,
            domain=m.domain,
            category=m.category,
            evidence_snippet=m.evidence_snippet,
            extraction_method=m.extraction_method,
            frequency=m.frequency,
        )
        for m in matched_skills
    ]

    # Add skill objects (cascade will save with resume)
    for skill in skill_objects:
        db.add(skill)

    # --- Step 3: ML Classification ---
    classification = classification_service.predict(extraction.text)

    resume.predicted_domain = classification.predicted_domain
    resume.prediction_confidence = classification.confidence_label

    # Decide final status
    if classification.is_uncertain:
        resume.status = ProcessingStatus.NEEDS_REVIEW
    else:
        resume.status = ProcessingStatus.COMPLETED

    resume.processed_at = datetime.datetime.now(datetime.timezone.utc)
    logger.info(
        "Processed resume %s: domain=%s confidence=%s skills=%d",
        resume.public_id,
        resume.predicted_domain,
        resume.prediction_confidence,
        len(skill_objects),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=ResumeDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a resume PDF",
)
async def upload_resume(
    request: Request,
    current_user: HRUser,
    file: UploadFile = File(...),
    candidate_reference: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> Resume:
    """
    Upload a PDF resume. The file is:
      1. Validated (extension, MIME, magic bytes, size limit).
      2. Stored under a server-generated UUID filename.
      3. Processed synchronously (text extraction → skill extraction → classification).
      4. Persisted with full results.

    Returns the Resume record with extracted skills.
    The raw PDF text is NOT included in the response.
    """
    content = await file.read()
    original_filename = file.filename or "unnamed.pdf"

    # --- Validate ---
    try:
        pdf_service.validate_upload(
            filename=original_filename,
            content=content,
            content_type=file.content_type,
        )
    except PDFValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # --- Save file ---
    stored_filename = pdf_service.generate_stored_filename(original_filename)
    try:
        file_path = pdf_service.save_upload(content, stored_filename)
    except OSError as exc:
        logger.error("Failed to save upload (details suppressed).")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store the uploaded file. Please try again.",
        )

    # --- Create or find candidate ---
    candidate: Candidate | None = None
    if candidate_reference:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.reference_code == candidate_reference)
            .first()
        )
        if not candidate:
            candidate = Candidate(reference_code=candidate_reference)
            db.add(candidate)
            db.flush()

    # --- Create Resume record ---
    resume = Resume(
        candidate_id=candidate.id if candidate else None,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_size_bytes=len(content),
        mime_type=file.content_type or "application/pdf",
        status=ProcessingStatus.UPLOADED,
        uploaded_by=current_user.id,
    )
    db.add(resume)
    db.flush()  # get resume.id before processing

    # --- Run pipeline ---
    _run_processing_pipeline(resume, file_path, db)

    db.commit()
    db.refresh(resume)

    # --- Audit ---
    audit_service.log_resume_access(
        db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        resume_public_id=resume.public_id,
        action="upload",
        ip_address=request.client.host if request.client else None,
    )

    return resume


@router.get("", response_model=List[ResumeRead], summary="List resumes")
def list_resumes(
    current_user: AnyAuthUser,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
) -> list[Resume]:
    """
    List resumes.
    - Admin/HR: see all resumes.
    - Readonly: see only resumes they uploaded (none, typically — readonly role is view-only).
    """
    q = db.query(Resume)
    if current_user.role == "readonly":
        q = q.filter(Resume.uploaded_by == current_user.id)
    if status_filter and status_filter in ProcessingStatus.ALL:
        q = q.filter(Resume.status == status_filter)
    return q.order_by(Resume.uploaded_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeDetailRead, summary="Get resume detail")
def get_resume(
    resume_id: str,
    request: Request,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> Resume:
    """Get a resume by public_id, including extracted skills. Text is never returned."""
    resume = _get_resume_or_404(db, resume_id)

    # Readonly users can only see resumes they uploaded
    if current_user.role == "readonly" and resume.uploaded_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    audit_service.log_resume_access(
        db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        resume_public_id=resume.public_id,
        action="view",
        ip_address=request.client.host if request.client else None,
    )

    return resume


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Archive a resume (admin only)",
)
def archive_resume(
    resume_id: str,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> dict:
    """Mark a resume as failed/archived. The file on disk is NOT deleted (audit trail)."""
    resume = _get_resume_or_404(db, resume_id)
    resume.status = ProcessingStatus.FAILED
    resume.error_message = f"Archived by admin {current_user.email}."
    db.commit()
    return {"detail": f"Resume {resume_id} archived."}
