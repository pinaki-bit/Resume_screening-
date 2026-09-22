"""
backend/app/services/ranking_service.py

Candidate ranking service.

Ranks ScreeningResult records for a given job by relevance_score descending.
Produces a structured ranked list for the UI with rank, tier, and summary.

Tiers:
  Excellent  — relevance_score ≥ 75
  Good       — relevance_score ≥ 55
  Fair       — relevance_score ≥ 35
  Low Match  — relevance_score < 35

Ethical constraint:
  - Ranking is NEVER performed on protected characteristics.
  - Ranking uses ONLY: required_coverage, preferred_coverage, skill count.
  - All tie-breaking is by screened_at timestamp (first-in order is neutral).
  - The score breakdown is always returned for human reviewers to inspect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.screening import ScreeningResult


TIER_EXCELLENT = 75.0
TIER_GOOD = 55.0
TIER_FAIR = 35.0


@dataclass
class RankedCandidate:
    rank: int
    tier: str                       # "Excellent" | "Good" | "Fair" | "Low Match"
    screening_result_id: int
    public_id: str
    candidate_id: int | None
    resume_id: int
    relevance_score: float
    required_coverage: float | None
    preferred_coverage: float | None
    predicted_domain: str | None
    prediction_confidence: str | None
    review_status: str
    matched_required_count: int
    missing_required_count: int
    score_breakdown: dict[str, Any] | None


def _tier(score: float) -> str:
    if score >= TIER_EXCELLENT:
        return "Excellent"
    if score >= TIER_GOOD:
        return "Good"
    if score >= TIER_FAIR:
        return "Fair"
    return "Low Match"


def rank_results_for_job(
    db: Session,
    job_id: int,
    review_status_filter: str | None = None,
) -> list[RankedCandidate]:
    """
    Fetch and rank all ScreeningResults for a job.

    Returns a sorted list with rank index and tier annotation.
    """
    import json

    q = db.query(ScreeningResult).filter(ScreeningResult.job_id == job_id)
    if review_status_filter:
        q = q.filter(ScreeningResult.review_status == review_status_filter)

    results = q.all()

    # Sort: relevance_score DESC, then screened_at ASC (FIFO tie-break — neutral)
    results.sort(
        key=lambda r: (-(r.relevance_score or 0.0), r.screened_at)
    )

    ranked: list[RankedCandidate] = []
    for rank, r in enumerate(results, start=1):
        # Parse JSON skill lists
        try:
            matched_req = json.loads(r.matched_required_skills or "[]")
        except Exception:
            matched_req = []
        try:
            missing_req = json.loads(r.missing_required_skills or "[]")
        except Exception:
            missing_req = []
        try:
            breakdown = json.loads(r.score_breakdown or "null")
        except Exception:
            breakdown = None

        score = r.relevance_score or 0.0
        ranked.append(RankedCandidate(
            rank=rank,
            tier=_tier(score),
            screening_result_id=r.id,
            public_id=r.public_id,
            candidate_id=r.candidate_id,
            resume_id=r.resume_id,
            relevance_score=round(score, 2),
            required_coverage=r.required_skill_coverage,
            preferred_coverage=r.preferred_skill_coverage,
            predicted_domain=r.predicted_domain,
            prediction_confidence=r.prediction_confidence,
            review_status=r.review_status,
            matched_required_count=len(matched_req),
            missing_required_count=len(missing_req),
            score_breakdown=breakdown,
        ))

    return ranked
