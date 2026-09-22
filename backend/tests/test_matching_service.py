"""
backend/tests/test_matching_service.py

Unit tests for the skill-matching formula.
Tests edge cases, weight normalization, and explainability output.
"""

from __future__ import annotations

import pytest
from app.services.matching_service import compute_match


class TestExactMatches:
    def test_all_required_matched(self):
        req = [("Python", 1.0), ("SQL", 1.0)]
        pref = []
        result = compute_match(req, pref, {"Python", "SQL"})
        assert result.required_coverage == 100.0
        assert result.combined_match == 100.0
        assert result.warning is None

    def test_no_required_matched(self):
        req = [("Python", 1.0), ("SQL", 1.0)]
        pref = []
        result = compute_match(req, pref, set())
        assert result.required_coverage == 0.0
        assert result.combined_match == 0.0
        assert len(result.missing_required) == 2

    def test_partial_required_match(self):
        req = [("Python", 1.0), ("SQL", 1.0)]
        pref = []
        result = compute_match(req, pref, {"Python"})
        assert result.required_coverage == 50.0
        assert "SQL" in result.missing_required
        assert "Python" in result.matched_required


class TestPreferredSkills:
    def test_preferred_boosts_score(self):
        req = [("Python", 1.0)]
        pref = [("TensorFlow", 1.0)]
        result = compute_match(req, pref, {"Python", "TensorFlow"})
        assert result.combined_match == 100.0

    def test_preferred_missing_does_not_make_combined_zero(self):
        req = [("Python", 1.0)]
        pref = [("TensorFlow", 1.0)]
        result = compute_match(req, pref, {"Python"})
        # Required fully matched → combined > 0
        assert result.required_coverage == 100.0
        assert result.combined_match > 0.0
        assert result.combined_match < 100.0

    def test_no_preferred_skills(self):
        req = [("Python", 1.0)]
        pref = []
        result = compute_match(req, pref, {"Python"})
        assert result.required_coverage == 100.0
        assert result.combined_match == 100.0


class TestEdgeCases:
    def test_no_skills_at_all(self):
        result = compute_match([], [], set())
        assert result.combined_match == 0.0
        assert result.warning is not None
        assert "Insufficient" in result.warning

    def test_case_insensitive_matching(self):
        req = [("python", 1.0)]
        result = compute_match(req, [], {"Python"})
        assert result.required_coverage == 100.0

    def test_score_clamped_to_100(self):
        req = [("Python", 1.0)]
        pref = [("SQL", 1.0)]
        result = compute_match(req, pref, {"Python", "SQL"})
        assert 0.0 <= result.combined_match <= 100.0

    def test_score_clamped_to_0(self):
        req = [("Python", 1.0)]
        result = compute_match(req, [], set())
        assert result.combined_match == 0.0

    def test_weighted_requirements(self):
        """High-weight required skill should have more impact."""
        req = [("Python", 2.0), ("SQL", 1.0)]  # Python is twice as important
        result_python = compute_match(req, [], {"Python"})
        result_sql = compute_match(req, [], {"SQL"})
        assert result_python.required_coverage > result_sql.required_coverage


class TestExplainability:
    def test_breakdown_contains_formula(self):
        req = [("Python", 1.0)]
        result = compute_match(req, [], {"Python"})
        assert "formula" in result.score_breakdown
        assert "label" in result.score_breakdown

    def test_breakdown_label_not_probability(self):
        req = [("Python", 1.0)]
        result = compute_match(req, [], {"Python"})
        label = result.score_breakdown.get("label", "")
        assert "probability" in label or "skill_match" in label
