"""
ml/src/preprocessing.py

Text preprocessing pipeline for resume classification.

Design:
  - Preprocessing is fit ONLY on training data to prevent data leakage.
  - The fitted TF-IDF vectorizer is saved as part of the sklearn Pipeline.
  - Text cleaning is deterministic (no learned state) and applied before fitting.
  - Random seeds are fixed for reproducibility.
"""

from __future__ import annotations

import re
import unicodedata


# ---------------------------------------------------------------------------
# Text cleaning (deterministic — no fitting)
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Clean and normalize resume text for ML input.

    Applied BEFORE TF-IDF fitting or transformation.
    Operations are deterministic and stateless.
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize Unicode (NFC)
    text = unicodedata.normalize("NFC", text)

    # Expand common ligatures
    ligature_map = {
        "\ufb01": "fi", "\ufb02": "fl", "\ufb00": "ff",
        "\ufb03": "ffi", "\ufb04": "ffl",
    }
    for char, repl in ligature_map.items():
        text = text.replace(char, repl)

    # Lowercase
    text = text.lower()

    # Preserve version numbers and common tech patterns before stripping
    # e.g. "python3.9", "c++", "node.js", "ci/cd", "aws-s3"
    # Replace sequences of special chars that are NOT part of tech terms
    text = re.sub(r"[^a-z0-9\s\.\-\+\#\/\_]", " ", text)

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# sklearn preprocessing pipeline components
# ---------------------------------------------------------------------------

def build_feature_pipeline(
    max_features: int = 50_000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int = 2,
    sublinear_tf: bool = True,
):
    """
    Build a TF-IDF feature extraction pipeline.

    Args:
        max_features: Maximum vocabulary size.
        ngram_range:  Unigrams + bigrams by default.
        min_df:       Minimum document frequency.
        sublinear_tf: Apply log(1+tf) scaling.

    Returns:
        sklearn TfidfVectorizer configured for resume text.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    return TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        sublinear_tf=sublinear_tf,
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"(?u)\b[a-z0-9][a-z0-9\.\-\+\#\/\_]{0,30}\b",
        stop_words="english",  # Use built-in english stopwords to reduce noise
    )
