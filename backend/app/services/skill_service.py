"""
backend/app/services/skill_service.py

Skill extraction service using spaCy PhraseMatcher.

Loads the skill taxonomy from shared/skill_taxonomy.json and builds a
PhraseMatcher at startup. The matcher is rebuilt when the taxonomy changes.

Design:
  - PhraseMatcher uses LOWER attribute for case-insensitive matching.
  - Each match returns a canonical skill name, domain, category, and evidence snippet.
  - Aliases are indexed to canonical names.
  - Duplicate matches for the same canonical skill are deduplicated; frequency is counted.

Security:
  - Resume text is processed in memory only; never logged.
  - Evidence snippets are limited to 200 characters.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

SNIPPET_WINDOW = 100   # chars of context around a match for evidence snippets
MAX_SNIPPET_LEN = 200  # max chars in the evidence snippet


@dataclass
class SkillMatch:
    canonical_name: str
    matched_text: str
    domain: str
    category: str
    evidence_snippet: str
    extraction_method: str = "phrase_matcher"
    frequency: int = 1


def _load_taxonomy() -> dict:
    """Load the skill taxonomy JSON from the shared directory."""
    from app.config import get_settings
    settings = get_settings()
    path = Path(settings.skill_taxonomy_path)
    if not path.exists():
        logger.error("Skill taxonomy not found at %s", path)
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _build_matcher():
    """
    Build and cache a spaCy PhraseMatcher from the skill taxonomy.

    Returns:
        (matcher, alias_map, skill_meta)
        - matcher: spaCy PhraseMatcher instance
        - alias_map: dict mapping lowercase phrase → (canonical, domain, category)
        - nlp: the spaCy nlp object (needed for tokenization in match_skills)
    """
    try:
        import spacy
        from spacy.matcher import PhraseMatcher
    except ImportError:
        logger.error("spaCy not installed — skill extraction disabled.")
        return None, {}, None

    from app.config import get_settings
    settings = get_settings()

    try:
        nlp = spacy.load(settings.spacy_model, disable=["ner", "parser"])
    except OSError:
        logger.error(
            "spaCy model '%s' not found — skill extraction disabled.", settings.spacy_model
        )
        return None, {}, None

    taxonomy = _load_taxonomy()
    if not taxonomy:
        return None, {}, None

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    alias_map: dict[str, tuple[str, str, str]] = {}  # phrase → (canonical, domain, cat)

    domains = taxonomy.get("domains", {})
    for domain_name, categories in domains.items():
        for category_name, skills in categories.items():
            for canonical_name, aliases in skills.items():
                all_phrases = [canonical_name.lower()] + [a.lower() for a in aliases]
                # Deduplicate
                seen = set()
                unique_phrases = []
                for phrase in all_phrases:
                    if phrase not in seen:
                        seen.add(phrase)
                        unique_phrases.append(phrase)

                patterns = [nlp.make_doc(phrase) for phrase in unique_phrases]
                rule_id = f"{domain_name}::{category_name}::{canonical_name}"
                matcher.add(rule_id, patterns)

                for phrase in unique_phrases:
                    alias_map[phrase] = (canonical_name, domain_name, category_name)

    logger.info(
        "PhraseMatcher built: %d rules, %d aliases across %d domains.",
        len(matcher), len(alias_map), len(domains),
    )
    return matcher, alias_map, nlp


def match_skills(text: str) -> list[SkillMatch]:
    """
    Extract skills from resume text using the PhraseMatcher.

    Returns a list of SkillMatch objects (deduplicated; frequency tracked).
    Returns an empty list if spaCy or the taxonomy is unavailable.
    """
    if not text or not text.strip():
        return []

    matcher, alias_map, nlp = _build_matcher()
    if matcher is None or nlp is None:
        return []

    doc = nlp(text[:nlp.max_length - 1])
    matches = matcher(doc)

    # Aggregate by canonical name
    seen: dict[str, SkillMatch] = {}

    for match_id, start, end in matches:
        span = doc[start:end]
        matched_text = span.text
        phrase_lower = matched_text.lower()

        if phrase_lower not in alias_map:
            continue

        canonical, domain, category = alias_map[phrase_lower]

        # Build evidence snippet (limited, safe context)
        char_start = max(0, span.start_char - SNIPPET_WINDOW)
        char_end = min(len(text), span.end_char + SNIPPET_WINDOW)
        snippet = text[char_start:char_end].replace("\n", " ").strip()
        if len(snippet) > MAX_SNIPPET_LEN:
            snippet = snippet[:MAX_SNIPPET_LEN] + "…"

        if canonical in seen:
            seen[canonical].frequency += 1
        else:
            seen[canonical] = SkillMatch(
                canonical_name=canonical,
                matched_text=matched_text,
                domain=domain,
                category=category,
                evidence_snippet=snippet,
            )

    return list(seen.values())


def invalidate_skill_cache() -> None:
    """Force rebuild of the PhraseMatcher on next call (e.g. after taxonomy update)."""
    _build_matcher.cache_clear()
    logger.info("PhraseMatcher cache cleared — will rebuild on next call.")
