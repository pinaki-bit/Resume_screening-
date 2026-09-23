"""
backend/app/api/v1/analytics.py

Analytics endpoints — summary statistics for dashboards and heatmaps.

GET /api/v1/analytics/summary        — high-level stats
GET /api/v1/analytics/domain-dist    — resume domain distribution
GET /api/v1/analytics/skill-heatmap  — top skills by domain
GET /api/v1/analytics/score-hist     — relevance score distribution
GET /api/v1/analytics/review-status  — pending/approved/rejected counts
"""


import logging
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.screening import ScreeningResult
from app.models.skill import ExtractedSkill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """High-level system summary for the dashboard."""
    total_resumes = db.query(Resume).count()
    processed_resumes = db.query(Resume).filter(
        Resume.status.in_(["completed", "needs_review"])
    ).count()
    total_jobs = db.query(Job).filter(Job.is_active == True).count()  # noqa: E712
    total_candidates = db.query(Candidate).count()
    pending_reviews = db.query(ScreeningResult).filter(
        ScreeningResult.review_status == "pending"
    ).count()
    model_unavailable = db.query(Resume).filter(
        Resume.prediction_confidence == "unavailable"
    ).count()

    return {
        "total_resumes": total_resumes,
        "processed_resumes": processed_resumes,
        "processing_rate_pct": (
            round(100 * processed_resumes / total_resumes, 1) if total_resumes > 0 else 0.0
        ),
        "total_active_jobs": total_jobs,
        "total_candidates": total_candidates,
        "pending_reviews": pending_reviews,
        "model_unavailable_count": model_unavailable,
    }


@router.get("/domain-dist")
def get_domain_distribution(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Domain distribution of processed resumes.
    Returns counts and percentages for each predicted domain.
    """
    rows = (
        db.query(Resume.predicted_domain, func.count(Resume.id))
        .filter(Resume.predicted_domain.isnot(None))
        .group_by(Resume.predicted_domain)
        .all()
    )
    total = sum(count for _, count in rows)
    distribution = [
        {
            "domain": domain or "Unknown",
            "count": count,
            "percentage": round(100 * count / total, 1) if total > 0 else 0.0,
        }
        for domain, count in sorted(rows, key=lambda x: -x[1])
    ]
    return {"total": total, "distribution": distribution}


@router.get("/skill-heatmap")
def get_skill_heatmap(
    current_user: AnyAuthUser,
    top_n: int = 15,
    db: Session = Depends(get_db),
) -> dict:
    """
    Top N skills per domain — suitable for rendering a skill frequency heatmap.
    Returns a matrix structure: {domain: {skill: count}}.
    """
    rows = (
        db.query(
            ExtractedSkill.domain,
            ExtractedSkill.canonical_name,
            func.sum(ExtractedSkill.frequency).label("total_freq"),
        )
        .filter(ExtractedSkill.domain.isnot(None))
        .group_by(ExtractedSkill.domain, ExtractedSkill.canonical_name)
        .order_by(ExtractedSkill.domain, func.sum(ExtractedSkill.frequency).desc())
        .all()
    )

    # Group by domain, take top N per domain
    from collections import defaultdict
    domain_skills: dict[str, list[dict]] = defaultdict(list)

    for domain, skill, freq in rows:
        if len(domain_skills[domain]) < top_n:
            domain_skills[domain].append({"skill": skill, "frequency": int(freq)})

    return {"domains": dict(domain_skills), "top_n": top_n}


@router.get("/score-hist")
def get_score_distribution(
    current_user: AnyAuthUser,
    job_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Histogram of relevance scores across all screening results.
    Buckets: 0-20, 20-40, 40-60, 60-80, 80-100.
    """
    q = db.query(ScreeningResult.relevance_score).filter(
        ScreeningResult.relevance_score.isnot(None)
    )
    if job_id:
        from app.models.job import Job
        job = db.query(Job).filter(Job.public_id == job_id).first()
        if job:
            q = q.filter(ScreeningResult.job_id == job.id)

    scores = [row[0] for row in q.all()]

    buckets = {
        "0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0
    }
    for s in scores:
        if s < 20:
            buckets["0-20"] += 1
        elif s < 40:
            buckets["20-40"] += 1
        elif s < 60:
            buckets["40-60"] += 1
        elif s < 80:
            buckets["60-80"] += 1
        else:
            buckets["80-100"] += 1

    return {
        "total_screened": len(scores),
        "mean_score": round(sum(scores) / len(scores), 2) if scores else None,
        "buckets": [
            {"range": k, "count": v, "percentage": round(100 * v / len(scores), 1) if scores else 0.0}
            for k, v in buckets.items()
        ],
    }


@router.get("/review-status")
def get_review_status_summary(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """Count of screening results by review status."""
    rows = (
        db.query(ScreeningResult.review_status, func.count(ScreeningResult.id))
        .group_by(ScreeningResult.review_status)
        .all()
    )
    return {
        "counts": {status: count for status, count in rows},
        "total": sum(count for _, count in rows),
    }
