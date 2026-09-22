"""
ml/scripts/train_model.py

Model training script.

Usage:
    python ml/scripts/train_model.py \\
        --data ml/data/raw/resumes.csv \\
        --text-col Resume \\
        --label-col Category \\
        --output ml/artifacts \\
        --seed 42

This script:
  1. Loads and validates the dataset.
  2. Applies label normalization from shared/label_mapping.json.
  3. Cleans text (deterministic, stateless).
  4. Performs stratified train/val/test split.
  5. Fits TF-IDF vectorizer on TRAINING data only.
  6. Trains all three baseline classifiers.
  7. Selects the best model by validation macro-F1.
  8. Evaluates on the held-out test set.
  9. Saves the pipeline artifact and metadata.
  10. Writes a full evaluation report.

NEVER use test-set information during model selection.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TARGET_CATEGORIES = [
    "Data Science",
    "Web Development",
    "Cloud Computing",
    "DevOps",
    "Cybersecurity",
]


def load_and_prepare(
    data_path: str,
    text_col: str,
    label_col: str,
    mapping_path: str,
) -> tuple:
    """Load, normalize labels, and clean text. Returns (X, y)."""
    import pandas as pd
    from ml.src.preprocessing import clean_text

    df = pd.read_csv(data_path)

    missing = [c for c in [text_col, label_col] if c not in df.columns]
    if missing:
        print(f"ERROR: Columns not found: {missing}")
        print(f"Available: {list(df.columns)}")
        sys.exit(1)

    # Load label mapping
    with open(mapping_path, "r") as f:
        mapping_data = json.load(f)
    label_map = {m["dataset_label"]: m["canonical"] for m in mapping_data["mappings"]}

    # Normalize labels
    df["_canonical"] = df[label_col].map(label_map)

    before = len(df)
    df = df[df["_canonical"].isin(TARGET_CATEGORIES)].copy()
    after = len(df)
    excluded = before - after
    if excluded > 0:
        print(f"INFO: Excluded {excluded} rows with unmapped labels.")

    df = df.dropna(subset=[text_col])
    df["_cleaned"] = df[text_col].astype(str).apply(clean_text)
    # Remove rows with very short text after cleaning
    df = df[df["_cleaned"].str.len() >= 50]

    print(f"\nTraining data: {len(df)} samples across {df['_canonical'].nunique()} categories")
    print(df["_canonical"].value_counts().to_string())

    return df["_cleaned"].tolist(), df["_canonical"].tolist()


def train(
    data_path: str,
    text_col: str,
    label_col: str,
    output_dir: str,
    seed: int = 42,
) -> None:
    import numpy as np
    import joblib
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import LinearSVC
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import classification_report, f1_score
    from ml.src.preprocessing import build_feature_pipeline

    mapping_path = str(PROJECT_ROOT / "shared" / "label_mapping.json")
    X, y = load_and_prepare(data_path, text_col, label_col, mapping_path)

    if len(X) < 50:
        print("ERROR: Fewer than 50 usable samples after filtering. Cannot train.")
        sys.exit(1)

    # Stratified split: 70% train, 15% val, 15% test
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=seed
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval,
        test_size=(0.15 / 0.85),  # ~15% of total
        stratify=y_trainval,
        random_state=seed,
    )
    print(f"\nSplit: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

    # Build candidates
    tfidf = build_feature_pipeline()

    candidates = {
        "LogisticRegression": Pipeline([
            ("tfidf", tfidf),
            ("clf", LogisticRegression(
                max_iter=1000, C=1.0, class_weight="balanced",
                random_state=seed, solver="lbfgs"
            )),
        ]),
        "LinearSVC": Pipeline([
            ("tfidf", build_feature_pipeline()),
            ("clf", LinearSVC(
                max_iter=2000, C=1.0, class_weight="balanced", random_state=seed
            )),
        ]),
        "MultinomialNB": Pipeline([
            ("tfidf", build_feature_pipeline(sublinear_tf=False)),
            ("clf", MultinomialNB(alpha=0.1)),
        ]),
    }

    # Evaluate each on validation set
    val_scores = {}
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        val_preds = pipeline.predict(X_val)
        f1 = f1_score(y_val, val_preds, average="macro", zero_division=0)
        val_scores[name] = f1
        print(f"  {name:25s}  val macro-F1 = {f1:.4f}")

    best_name = max(val_scores, key=val_scores.get)
    print(f"\nBest model: {best_name} (val macro-F1={val_scores[best_name]:.4f})")

    # Re-train best model on train+val combined
    best_pipeline = candidates[best_name]
    best_pipeline.fit(X_train + X_val, y_train + y_val)

    # Evaluate on held-out test set
    test_preds = best_pipeline.predict(X_test)
    test_f1_macro = f1_score(y_test, test_preds, average="macro", zero_division=0)
    test_f1_weighted = f1_score(y_test, test_preds, average="weighted", zero_division=0)
    report = classification_report(y_test, test_preds, zero_division=0)

    print(f"\n{'='*60}")
    print(f"TEST SET EVALUATION ({best_name})")
    print(f"{'='*60}")
    print(report)
    print(f"Macro F1:    {test_f1_macro:.4f}")
    print(f"Weighted F1: {test_f1_weighted:.4f}")

    # Save artifact
    version_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    artifact = {
        "pipeline": best_pipeline,
        "version": version_tag,
        "model_name": best_name,
        "classes": list(best_pipeline.classes_),
        "training_samples": len(X_train) + len(X_val),
        "test_samples": len(X_test),
        "random_seed": seed,
        "val_macro_f1": val_scores[best_name],
        "test_macro_f1": test_f1_macro,
        "test_weighted_f1": test_f1_weighted,
        "classification_report": report,
        "trained_at": datetime.datetime.utcnow().isoformat(),
    }

    artifact_file = output_path / f"model_{version_tag}.joblib"
    latest_link = output_path / "model_latest.joblib"

    joblib.dump(artifact, artifact_file)
    joblib.dump(artifact, latest_link)
    print(f"\nArtifact saved: {artifact_file}")
    print(f"Latest link:    {latest_link}")

    # Save JSON metadata
    meta = {k: v for k, v in artifact.items() if k != "pipeline"}
    with (output_path / f"model_{version_tag}_metadata.json").open("w") as f:
        json.dump(meta, f, indent=2, default=str)

    print("\nTraining complete.")


def main():
    parser = argparse.ArgumentParser(description="Train the resume classification model.")
    parser.add_argument("--data", required=True, help="Path to dataset CSV.")
    parser.add_argument("--text-col", default="Resume")
    parser.add_argument("--label-col", default="Category")
    parser.add_argument("--output", default="ml/artifacts")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train(args.data, args.text_col, args.label_col, args.output, args.seed)


if __name__ == "__main__":
    main()
