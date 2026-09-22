"""
backend/app/schemas/job.py

Pydantic v2 schemas for Job and JobRequirement.
"""

from __future__ import annotations

import datetime
from typing import List

from pydantic import BaseModel, Field


class JobRequirementCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=128)
    is_required: bool = True
    weight: float = Field(default=1.0, ge=0.01, le=10.0)
    notes: str | None = None


class JobRequirementRead(BaseModel):
    id: int
    job_id: int
    skill_name: str
    is_required: bool
    weight: float
    notes: str | None

    model_config = {"from_attributes": True}


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    department: str | None = None
    description: str | None = None
    domain: str | None = None
    requirements: List[JobRequirementCreate] = Field(default_factory=list)


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = None
    description: str | None = None
    domain: str | None = None
    is_active: bool | None = None


class JobRead(BaseModel):
    id: int
    public_id: str
    title: str
    department: str | None
    description: str | None
    domain: str | None
    is_active: bool
    created_by: int | None
    requirements: List[JobRequirementRead]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}
