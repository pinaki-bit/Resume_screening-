"""
backend/app/services/classification_service.py

ML model loading and inference service.

Responsibilities:
  - Load the trained scikit-learn pipeline artifact at startup.
  - Serve inference requests from the resume processing pipeline.
  - Return structured prediction results with appropriate uncertainty signals.
  - NEVER retrain or replace the model at runtime from a user request.

Security:
  - Resume text is never logged.
  - Model artifacts are loaded from a configured path only; no dynamic loading from uploads.

Confidence levels:
  - high:   max class probability ≥ 0.70
  - medium: max class probability ≥ 0.45
  - low:    max class probability < 0.45 → "uncertain" / review state

If the model is not available (artifact not found), inference returns a safe
"MODEL_UNAVAILABLE" state rather than failing the entire upload.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

TARGET_CATEGORIES = {
    "Data Science",
    "Web Development",
    "Cloud Computing",
    "DevOps",
    "Cybersecurity",
}

CONFIDENCE_HIGH = 0.70
CONFIDENCE_MEDIUM = 0.45


@dataclass
class ClassificationResult:
    predicted_domain: str | None
    confidence_label: str          # "high" | "medium" | "low" | "unavailable"
    top_probability: float | None  # None if model not calibrated / not available
    all_probabilities: dict[str, float] | None
    model_version: str | None
    is_uncertain: bool
    warning: str | None


@lru_cache(maxsize=1)
def _load_model() -> tuple[Any, str, dict[str, Any]] | None:
    """
    Load the trained pipeline artifact.

    Returns:
        (pipeline, version_tag, artifact_dict) or None if unavailable.
    """
    from app.config import get_settings
    import joblib
    settings = get_settings()

    model_path = Path(settings.active_model_path)
    if not model_path.exists():
        logger.warning(
            "Model artifact not found at %s. "
            "Train a model first using ml/scripts/train_model.py",
            model_path,
        )
        return None

    try:
        artifact = joblib.load(model_path)
        # Artifact is expected to be a dict: {"pipeline": ..., "version": ..., "classes": ...}
        pipeline = artifact.get("pipeline")
        version = artifact.get("version", "unknown")
        logger.info("Classification model v%s loaded from %s.", version, model_path.name)
        return pipeline, version, artifact
    except Exception as exc:
        logger.error("Failed to load model artifact: %s", exc)
        return None


def predict(text: str) -> ClassificationResult:
    """
    Classify resume text into one of the five target domains.

    Args:
        text: Cleaned, extracted resume text.

    Returns:
        ClassificationResult with prediction, confidence, and explanation.
    """
    if not text or not text.strip():
        return ClassificationResult(
            predicted_domain=None,
            confidence_label="low",
            top_probability=None,
            all_probabilities=None,
            model_version=None,
            is_uncertain=True,
            warning="Input text is empty or too short for reliable classification.",
        )

    model_result = _load_model()
    if model_result is None:
        return ClassificationResult(
            predicted_domain=None,
            confidence_label="unavailable",
            top_probability=None,
            all_probabilities=None,
            model_version=None,
            is_uncertain=True,
            warning=(
                "Classification model is not available. "
                "Train a model using ml/scripts/train_model.py and restart the server."
            ),
        )

    pipeline, version, artifact = model_result

    try:
        predicted_label = pipeline.predict([text])[0]
        
        # XGBoost models might output integer labels that need decoding
        label_encoder = artifact.get("label_encoder") if artifact else None
        if label_encoder is not None and isinstance(predicted_label, (int, float, type(predicted_label).__bases__[0])): 
            # Decode the int back to string
            try:
                predicted_label = label_encoder.inverse_transform([int(predicted_label)])[0]
            except Exception:
                pass

        # Attempt to get probabilities (only if the classifier supports predict_proba)
        all_probs: dict[str, float] | None = None
        top_prob: float | None = None
        confidence_label = "medium"

        if hasattr(pipeline, "predict_proba"):
            probs = pipeline.predict_proba([text])[0]
            
            if label_encoder is not None:
                classes = label_encoder.inverse_transform(range(len(probs)))
            else:
                classes = pipeline.classes_
                
            all_probs = {str(cls): float(p) for cls, p in zip(classes, probs)}
            top_prob = float(max(probs))

            if top_prob >= CONFIDENCE_HIGH:
                confidence_label = "high"
            elif top_prob >= CONFIDENCE_MEDIUM:
                confidence_label = "medium"
            else:
                confidence_label = "low"
        elif hasattr(pipeline, "decision_function"):
            # LinearSVC — decision score is not a probability
            # We can still flag low-confidence cases via the score margin
            scores = pipeline.decision_function([text])[0]
            max_score = float(max(scores))
            # Heuristic: if the top score is close to the second, confidence is low
            sorted_scores = sorted(scores, reverse=True)
            margin = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else 0
            if margin > 1.0:
                confidence_label = "high"
            elif margin > 0.3:
                confidence_label = "medium"
            else:
                confidence_label = "low"

        is_uncertain = confidence_label == "low"
        warning = None
        if is_uncertain:
            warning = (
                "Classification confidence is low. This resume does not clearly fit "
                "any single domain. Human review is strongly recommended."
            )

        return ClassificationResult(
            predicted_domain=str(predicted_label),
            confidence_label=confidence_label,
            top_probability=top_prob,
            all_probabilities=all_probs,
            model_version=str(version),
            is_uncertain=is_uncertain,
            warning=warning,
        )

    except Exception as exc:
        logger.error("Inference error (details suppressed): %s", type(exc).__name__)
        return ClassificationResult(
            predicted_domain=None,
            confidence_label="unavailable",
            top_probability=None,
            all_probabilities=None,
            model_version=str(version),
            is_uncertain=True,
            warning="An error occurred during classification. Please try again.",
        )


def invalidate_model_cache() -> None:
    """Force reload of the model on next inference call."""
    _load_model.cache_clear()
    logger.info("Model cache cleared — will reload on next inference request.")
