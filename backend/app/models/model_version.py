"""
backend/app/models/model_version.py

ModelVersion ORM model.

Tracks every trained model artifact: filename, training metadata,
evaluation metrics, and deployment status.
Only one model may be "active" at a time.
"""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    version_tag: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    artifact_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Training provenance
    training_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    training_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Evaluation metrics (on held-out test set)
    test_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_macro_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_weighted_f1: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Full classification report stored as JSON string
    classification_report_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Deployment
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deployed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deployed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion tag={self.version_tag!r} "
            f"active={self.is_active} macro_f1={self.test_macro_f1}>"
        )
