"""
backend/app/api/v1/jobs.py

Job description endpoints.

POST   /api/v1/jobs                       — create job (hr, admin)
GET    /api/v1/jobs                       — list all active jobs (any auth user)
GET    /api/v1/jobs/{job_id}              — get job detail (any auth user)
PATCH  /api/v1/jobs/{job_id}              — update job (hr, admin)
DELETE /api/v1/jobs/{job_id}              — deactivate job (admin only)
POST   /api/v1/jobs/{job_id}/requirements — add requirement (hr, admin)
DELETE /api/v1/jobs/{job_id}/requirements/{req_id} — remove requirement (hr, admin)
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import AdminUser, AnyAuthUser, HRUser
from app.database import get_db
from app.models.job import Job, JobRequirement
from app.schemas.job import (
    JobCreate, JobRead, JobRequirementCreate, JobRequirementRead, JobUpdate
)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


def _get_job_or_404(db: Session, job_id: str) -> Job:
    """Fetch a job by public_id or raise 404."""
    job = db.query(Job).filter(Job.public_id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> Job:
    """Create a new job description."""
    job = Job(
        title=payload.title,
        department=payload.department,
        description=payload.description,
        domain=payload.domain,
        created_by=current_user.id,
    )
    db.add(job)
    db.flush()  # get job.id before adding requirements

    for req in payload.requirements or []:
        db.add(JobRequirement(
            job_id=job.id,
            skill_name=req.skill_name,
            is_required=req.is_required,
            weight=req.weight,
            notes=req.notes,
        ))

    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=List[JobRead])
def list_jobs(
    current_user: AnyAuthUser,
    active_only: bool = True,
    db: Session = Depends(get_db),
) -> list[Job]:
    """List job descriptions. By default only active jobs are returned."""
    q = db.query(Job)
    if active_only:
        q = q.filter(Job.is_active == True)  # noqa: E712
    return q.order_by(Job.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> Job:
    """Get a job description by its public ID."""
    return _get_job_or_404(db, job_id)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: str,
    payload: JobUpdate,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> Job:
    """Update a job description (title, description, domain, active status)."""
    job = _get_job_or_404(db, job_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def deactivate_job(
    job_id: str,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> dict:
    """Deactivate (soft-delete) a job description. Admin only."""
    job = _get_job_or_404(db, job_id)
    job.is_active = False
    db.commit()
    return {"detail": f"Job '{job.title}' deactivated."}


@router.post(
    "/{job_id}/requirements",
    response_model=JobRequirementRead,
    status_code=status.HTTP_201_CREATED,
)
def add_requirement(
    job_id: str,
    payload: JobRequirementCreate,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> JobRequirement:
    """Add a skill requirement to a job."""
    job = _get_job_or_404(db, job_id)
    req = JobRequirement(
        job_id=job.id,
        skill_name=payload.skill_name,
        is_required=payload.is_required,
        weight=payload.weight,
        notes=payload.notes,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.delete(
    "/{job_id}/requirements/{req_id}",
    status_code=status.HTTP_200_OK,
)
def remove_requirement(
    job_id: str,
    req_id: int,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> dict:
    """Remove a skill requirement from a job."""
    job = _get_job_or_404(db, job_id)
    req = db.query(JobRequirement).filter(
        JobRequirement.id == req_id,
        JobRequirement.job_id == job.id,
    ).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found."
        )
    db.delete(req)
    db.commit()
    return {"detail": "Requirement removed."}
