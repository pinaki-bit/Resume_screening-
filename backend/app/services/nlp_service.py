"""
backend/app/services/nlp_service.py

NLP pipeline for resume text analysis.

Uses spaCy (en_core_web_lg) for:
  - Named entity recognition (organizations, dates, locations)
  - Tokenization and lemmatization
  - PhraseMatcher-based skill extraction (delegated to skill_service)

This module manages the spaCy model lifecycle:
  - Model is loaded once at process startup and cached.
  - If the model is unavailable, the service degrades gracefully.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import NamedTuple

logger = logging.getLogger(__name__)


class NLPEntity(NamedTuple):
    text: str
    label: str   # spaCy entity label (ORG, DATE, GPE, etc.)
    start: int
    end: int


class NLPAnalysisResult(NamedTuple):
    entities: list[NLPEntity]
    # Summary counts by entity type
    organizations: list[str]
    dates: list[str]
    # Normalized token stream (lowercased lemmas, no stopwords)
    tokens: list[str]


@lru_cache(maxsize=1)
def _load_spacy_model():
    """Load and cache the spaCy model. Returns None if unavailable."""
    from app.config import get_settings
    settings = get_settings()
    try:
        import spacy
        nlp = spacy.load(settings.spacy_model)
        logger.info("spaCy model '%s' loaded successfully.", settings.spacy_model)
        return nlp
    except OSError:
        logger.error(
            "spaCy model '%s' not found. "
            "Run: python -m spacy download %s",
            settings.spacy_model, settings.spacy_model,
        )
        return None
    except ImportError:
        logger.error("spaCy is not installed.")
        return None


def get_nlp():
    """Return the cached spaCy model (or None if unavailable)."""
    return _load_spacy_model()


def analyze_text(text: str) -> NLPAnalysisResult:
    """
    Run the NLP pipeline on resume text.

    Returns extracted entities, organizations, dates, and a normalized token stream.
    Degrades gracefully if spaCy is not available.

    NOTE: This function processes user-supplied text. Ensure the text is never
    written to logs at DEBUG/INFO level (may contain PII).
    """
    if not text or not text.strip():
        return NLPAnalysisResult(entities=[], organizations=[], dates=[], tokens=[])

    nlp = get_nlp()
    if nlp is None:
        # Fallback: basic tokenization without NLP
        tokens = _basic_tokenize(text)
        return NLPAnalysisResult(entities=[], organizations=[], dates=[], tokens=tokens)

    # Truncate to spaCy's max length (avoid memory issues on very large resumes)
    max_len = min(len(text), nlp.max_length - 1)
    doc = nlp(text[:max_len])

    entities: list[NLPEntity] = []
    organizations: list[str] = []
    dates: list[str] = []

    for ent in doc.ents:
        entities.append(NLPEntity(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
        ))
        if ent.label_ in ("ORG", "COMPANY"):
            organizations.append(ent.text)
        elif ent.label_ in ("DATE", "TIME"):
            dates.append(ent.text)

    # Build a normalized token stream for downstream ML use
    tokens = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.lemma_) > 1
    ]

    return NLPAnalysisResult(
        entities=entities,
        organizations=list(set(organizations)),
        dates=dates,
        tokens=tokens,
    )


def _basic_tokenize(text: str) -> list[str]:
    """Minimal tokenizer used as fallback when spaCy is unavailable."""
    # Remove punctuation except hyphens and dots (needed for tech terms)
    text = re.sub(r"[^\w\s.\-+#]", " ", text.lower())
    return [t for t in text.split() if len(t) > 1]


def extract_structured_sections(text: str) -> dict[str, str | None]:
    """
    Attempt to extract major structured sections from resume text.
    Returns a dictionary of sections (Experience, Education, Certifications).
    """
    sections = {
        "experience": None,
        "education": None,
        "certifications": None,
    }
    
    # Common section header patterns
    patterns = {
        "experience": r"(?:^|\n)\s*(?:WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EXPERIENCE|EMPLOYMENT HISTORY)\s*[:\-]?\s*\n(.*?)(?=\n\s*[A-Z][A-Z\s]{3,}\s*[:\-]?\s*\n|\Z)",
        "education": r"(?:^|\n)\s*(?:EDUCATION|ACADEMIC BACKGROUND|ACADEMICS)\s*[:\-]?\s*\n(.*?)(?=\n\s*[A-Z][A-Z\s]{3,}\s*[:\-]?\s*\n|\Z)",
        "certifications": r"(?:^|\n)\s*(?:CERTIFICATIONS|LICENSES AND CERTIFICATIONS|CERTIFICATES)\s*[:\-]?\s*\n(.*?)(?=\n\s*[A-Z][A-Z\s]{3,}\s*[:\-]?\s*\n|\Z)",
    }
    
    for key, regex in patterns.items():
        match = re.search(regex, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
            
    return sections
