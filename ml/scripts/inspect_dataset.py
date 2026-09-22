"""
ml/scripts/inspect_dataset.py

Dataset inspection script — run BEFORE any training.

Usage:
    python ml/scripts/inspect_dataset.py --data ml/data/raw/resumes.csv

Output:
    - Printed report to console
    - JSON report saved to ml/artifacts/dataset_report.json

This script does NOT modify the dataset.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path so shared/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def inspect(data_path: str, text_col: str, label_col: str) -> dict:
    """Inspect the dataset and return a report dictionary."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas not installed. Run: pip install pandas")
        sys.exit(1)

    path = Path(data_path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    # Load
    print(f"\n{'='*60}")
    print(f"DATASET INSPECTION REPORT")
    print(f"{'='*60}")
    print(f"File: {path}")

    ext = path.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    elif ext == ".json":
        df = pd.read_json(path)
    else:
        print(f"ERROR: Unsupported format '{ext}'. Supported: csv, xlsx, json")
        sys.exit(1)

    report = {}

    # Basic info
    report["file_path"] = str(path)
    report["file_format"] = ext
    report["total_rows"] = len(df)
    report["total_columns"] = len(df.columns)
    report["columns"] = list(df.columns)
    report["dtypes"] = {col: str(df[col].dtype) for col in df.columns}

    print(f"\nShape: {df.shape}")
    print(f"\nColumns ({len(df.columns)}):")
    for col in df.columns:
        print(f"  - {col!r:30s} dtype={df[col].dtype}")

    # Text column
    if text_col not in df.columns:
        print(f"\nWARNING: Text column '{text_col}' not found.")
        print(f"Available columns: {list(df.columns)}")
        report["text_column_found"] = False
    else:
        report["text_column_found"] = True
        text_series = df[text_col].dropna().astype(str)
        lengths = text_series.str.len()
        report["text_stats"] = {
            "null_count": int(df[text_col].isna().sum()),
            "mean_length": round(float(lengths.mean()), 1),
            "median_length": float(lengths.median()),
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "empty_count": int((lengths == 0).sum()),
            "very_short_count": int((lengths < 100).sum()),
        }
        print(f"\nText column '{text_col}':")
        for k, v in report["text_stats"].items():
            print(f"  {k}: {v}")

    # Label column
    if label_col not in df.columns:
        print(f"\nWARNING: Label column '{label_col}' not found.")
        report["label_column_found"] = False
    else:
        report["label_column_found"] = True
        label_counts = df[label_col].value_counts()
        report["label_distribution"] = label_counts.to_dict()
        report["unique_labels"] = list(df[label_col].dropna().unique())
        report["null_labels"] = int(df[label_col].isna().sum())

        print(f"\nLabel column '{label_col}':")
        print(f"  Unique labels: {len(report['unique_labels'])}")
        print(f"  Null labels:   {report['null_labels']}")
        print(f"\nClass distribution:")
        for label, count in label_counts.items():
            pct = 100 * count / len(df)
            print(f"  {str(label):40s} {count:5d} ({pct:.1f}%)")

        # Check against target categories
        target_cats = {
            "Data Science", "Web Development", "Cloud Computing",
            "DevOps", "Cybersecurity"
        }

        # Load label mapping
        mapping_path = PROJECT_ROOT / "shared" / "label_mapping.json"
        if mapping_path.exists():
            with mapping_path.open() as f:
                mapping_data = json.load(f)
            canonical_map = {
                m["dataset_label"]: m["canonical"]
                for m in mapping_data.get("mappings", [])
            }
            unmapped = [
                str(lbl) for lbl in report["unique_labels"]
                if str(lbl) not in canonical_map
            ]
            mapped_to_target = {
                lbl: canonical_map[lbl]
                for lbl in report["unique_labels"]
                if lbl in canonical_map and canonical_map[lbl] in target_cats
            }
            report["mapped_to_target"] = mapped_to_target
            report["unmapped_labels"] = unmapped

            print(f"\nLabel mapping analysis:")
            print(f"  Labels that map to target categories: {len(mapped_to_target)}")
            for src, tgt in mapped_to_target.items():
                count = label_counts.get(src, 0)
                print(f"    {src!r:35s} -> {tgt!r}  ({count} samples)")
            if unmapped:
                print(f"\n  Labels NOT in mapping (will be excluded): {len(unmapped)}")
                for u in unmapped:
                    print(f"    {u!r}")

    # Duplicates
    dup_count = int(df.duplicated().sum())
    report["duplicate_rows"] = dup_count
    print(f"\nDuplicate rows: {dup_count}")

    # Potential PII columns (heuristic)
    pii_keywords = {"name", "email", "phone", "address", "dob", "birth", "gender", "photo"}
    pii_cols = [c for c in df.columns if any(k in c.lower() for k in pii_keywords)]
    report["potential_pii_columns"] = pii_cols
    if pii_cols:
        print(f"\nPotential PII columns detected: {pii_cols}")
        print("  Review these columns before training to ensure appropriate handling.")

    print(f"\n{'='*60}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Inspect the resume dataset.")
    parser.add_argument("--data", required=True, help="Path to the dataset file.")
    parser.add_argument(
        "--text-col", default="Resume",
        help="Column name containing resume text. Default: 'Resume'"
    )
    parser.add_argument(
        "--label-col", default="Category",
        help="Column name containing category labels. Default: 'Category'"
    )
    parser.add_argument(
        "--output", default="ml/artifacts/dataset_report.json",
        help="Output path for the JSON report."
    )
    args = parser.parse_args()

    report = inspect(args.data, args.text_col, args.label_col)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
