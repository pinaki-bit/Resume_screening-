"""
backend/app/services/matching_service.py

Transparent skill-match formula.

Formula (configurable weights):
  required_coverage   = Σ(weight of matched required skills)
                        ─────────────────────────────────── × 100
                        Σ(weight of all required skills)

  preferred_coverage  = Σ(weight of matched preferred skills)
                        ──────────────────────────────────────── × 100
                        Σ(weight of all preferred skills)

  combined_match      = (req_weight × required_coverage)
                      + (pref_weight × preferred_coverage)
                        ──────────────────────────────────
                        (req_weight + pref_weight)

  → Result is always in [0, 100]. Weights are normalized.

Edge cases:
  - No required skills: required_coverage = 100.0 (vacuously satisfied).
  - No preferred skills: preferred_coverage = 0.0 and pref_weight treated as 0.
  - No skills at all: return "insufficient requirements" warning.
  - Division by zero: impossible given above rules.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_REQUIRED_WEIGHT = 0.70   # 70% of combined score from required skills
DEFAULT_PREFERRED_WEIGHT = 0.30  # 30% from preferred skills


@dataclass
class MatchResult:
    required_coverage: float        # 0.0–100.0
    preferred_coverage: float       # 0.0–100.0
    combined_match: float           # 0.0–100.0
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    score_breakdown: dict           # explainability
    warning: str | None


def compute_match(
    required_skills: list[tuple[str, float]],    # [(skill_name, weight), ...]
    preferred_skills: list[tuple[str, float]],   # [(skill_name, weight), ...]
    candidate_skills: set[str],                  # canonical names, lowercased
    required_weight: float = DEFAULT_REQUIRED_WEIGHT,
    preferred_weight: float = DEFAULT_PREFERRED_WEIGHT,
) -> MatchResult:
    """
    Compute skill-match scores between a job's requirements and a candidate's skills.

    Args:
        required_skills:  List of (canonical_skill_name, weight) for required skills.
        preferred_skills: List of (canonical_skill_name, weight) for preferred skills.
        candidate_skills: Set of canonical skill names extracted from the candidate's resume.
        required_weight:  Relative weight of required coverage in the combined score.
        preferred_weight: Relative weight of preferred coverage in the combined score.

    Returns:
        MatchResult with full transparency breakdown.
    """
    # Normalize skill names for comparison
    candidate_lower = {s.lower() for s in candidate_skills}

    # --- Guard: no skills at all ---
    if not required_skills and not preferred_skills:
        return MatchResult(
            required_coverage=0.0,
            preferred_coverage=0.0,
            combined_match=0.0,
            matched_required=[],
            missing_required=[],
            matched_preferred=[],
            score_breakdown={},
            warning="Insufficient job requirements for skill-match scoring.",
        )

    # --- Required skills ---
    matched_req: list[str] = []
    missing_req: list[str] = []
    total_req_weight = 0.0
    matched_req_weight = 0.0

    for skill, weight in required_skills:
        total_req_weight += weight
        if skill.lower() in candidate_lower:
            matched_req.append(skill)
            matched_req_weight += weight
        else:
            missing_req.append(skill)

    if total_req_weight > 0:
        required_coverage = (matched_req_weight / total_req_weight) * 100.0
    else:
        # No required skills → vacuously satisfied
        required_coverage = 100.0

    # --- Preferred skills ---
    matched_pref: list[str] = []
    total_pref_weight = 0.0
    matched_pref_weight = 0.0

    for skill, weight in preferred_skills:
        total_pref_weight += weight
        if skill.lower() in candidate_lower:
            matched_pref.append(skill)
            matched_pref_weight += weight

    if total_pref_weight > 0:
        preferred_coverage = (matched_pref_weight / total_pref_weight) * 100.0
    else:
        preferred_coverage = 0.0
        preferred_weight = 0.0   # treat as absent

    # --- Combined score ---
    total_weight = required_weight + preferred_weight
    if total_weight == 0:
        combined_match = 0.0
    else:
        combined_match = (
            (required_weight * required_coverage)
            + (preferred_weight * preferred_coverage)
        ) / total_weight

    # Clamp to [0, 100] (should be guaranteed by formula, but defensive)
    combined_match = max(0.0, min(100.0, combined_match))

    # --- Explainability breakdown ---
    breakdown = {
        "formula": (
            "combined_match = "
            "(req_weight × required_coverage + pref_weight × preferred_coverage) "
            "/ (req_weight + pref_weight)"
        ),
        "required_coverage_pct": round(required_coverage, 2),
        "preferred_coverage_pct": round(preferred_coverage, 2),
        "required_weight_used": round(required_weight, 3),
        "preferred_weight_used": round(preferred_weight, 3),
        "matched_required_count": len(matched_req),
        "total_required_count": len(required_skills),
        "matched_preferred_count": len(matched_pref),
        "total_preferred_count": len(preferred_skills),
        "label": "skill_match_percentage (not a probability of job success)",
    }

    return MatchResult(
        required_coverage=round(required_coverage, 2),
        preferred_coverage=round(preferred_coverage, 2),
        combined_match=round(combined_match, 2),
        matched_required=matched_req,
        missing_required=missing_req,
        matched_preferred=matched_pref,
        score_breakdown=breakdown,
        warning=None,
    )


def extract_job_skills(
    requirements: list,  # list of JobRequirement ORM objects
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """
    Split job requirements into required and preferred lists.

    Returns:
        (required_skills, preferred_skills) — each is [(name, weight), ...]
    """
    required = [(r.skill_name, r.weight) for r in requirements if r.is_required]
    preferred = [(r.skill_name, r.weight) for r in requirements if not r.is_required]
    return required, preferred
