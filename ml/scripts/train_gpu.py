import os
import argparse
import time
import datetime
import pandas as pd
import json
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, f1_score
from xgboost import XGBClassifier
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ml.src.preprocessing import clean_text

def train(data_path, text_col, label_col, output_dir, seed=42):
    print("=" * 60)
    print("XGBOOST GPU-ACCELERATED MODEL TRAINING")
    print("=" * 60)

    # 1. Load Data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    if text_col not in df.columns or label_col not in df.columns:
        raise ValueError(f"Missing required columns. Found: {list(df.columns)}")

    df = df.dropna(subset=[text_col, label_col])
    initial_count = len(df)
    print(f"Loaded {initial_count} samples from {data_path}")

    # 2. Map Labels using mapping file
    mapping_file = Path(__file__).parent.parent.parent / "shared" / "label_mapping.json"
    canonical_map = {}
    if mapping_file.exists():
        with open(mapping_file, "r") as f:
            mapping_data = json.load(f)
            for m in mapping_data.get("mappings", []):
                canonical_map[m["dataset_label"]] = m["canonical"]
    
    df["_canonical"] = df[label_col].map(canonical_map)
    df = df.dropna(subset=["_canonical"])
    
    final_count = len(df)
    print(f"INFO: Retained {final_count} samples mapping to target domains.")
    if final_count == 0:
        raise ValueError("No matching data found.")

    print(df["_canonical"].value_counts())

    # 3. Clean Text
    print("Cleaning text...")
    df["_clean_text"] = df[text_col].apply(clean_text)
    
    # 4. Prepare Features & Labels
    X = df["_clean_text"].values
    
    le = LabelEncoder()
    y = le.fit_transform(df["_canonical"].values)

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=seed, stratify=y_temp)

    print(f"\nSplit: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}")

    # 5. Build GPU Pipeline
    print("\nTraining XGBoost on GPU...")
    start_time = time.time()
    
    # XGBClassifier using CUDA
    xgb = XGBClassifier(
        tree_method="hist",
        device="cuda",
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        random_state=seed,
        eval_metric="mlogloss",
        use_label_encoder=False
    )
    
    pipeline = ImbPipeline([
        ("tfidf", TfidfVectorizer(
            max_features=10000, 
            ngram_range=(1, 2), 
            stop_words="english",
            sublinear_tf=True
        )),
        ("smote", SMOTE(random_state=seed)),  # Handle class imbalance on CPU
        ("clf", xgb)
    ])
    
    pipeline.fit(X_train, y_train)
    
    train_time = time.time() - start_time
    print(f"Training completed in {train_time:.1f} seconds.")

    # 6. Evaluation
    print("\n" + "=" * 60)
    print("TEST SET EVALUATION")
    print("=" * 60)
    
    y_pred = pipeline.predict(X_test)
    
    target_names = le.inverse_transform(range(len(le.classes_)))
    print(classification_report(y_test, y_pred, target_names=target_names))
    
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")
    
    print(f"Macro F1:    {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")

    # 7. Save Model
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    model_filename = f"xgb_model_{timestamp}.joblib"
    model_path = os.path.join(output_dir, model_filename)
    
    # Save pipeline and label encoder
    bundle = {
        "pipeline": pipeline,
        "label_encoder": le,
        "metrics": {
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1)
        },
        "trained_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "model_type": "xgboost_gpu",
        "dataset_size": final_count
    }
    
    joblib.dump(bundle, model_path, compress=3)
    print(f"\nArtifact saved: {model_path}")
    
    # Symlink to latest
    latest_path = os.path.join(output_dir, "model_latest.joblib")
    if os.path.exists(latest_path) or os.path.islink(latest_path):
        try:
            os.remove(latest_path)
        except OSError:
            pass
            
    # For Windows, sometimes symlinks require admin. If it fails, copy.
    try:
        os.symlink(model_filename, latest_path)
    except OSError:
        import shutil
        shutil.copy2(model_path, latest_path)
        
    print(f"Latest link:    {latest_path}")
    print("\nTraining complete.")

def main():
    parser = argparse.ArgumentParser(description="Train XGBoost GPU Model")
    parser.add_argument("--data", required=True, help="Path to training data CSV")
    parser.add_argument("--text-col", default="Text", help="Name of text column")
    parser.add_argument("--label-col", default="Category", help="Name of label column")
    parser.add_argument("--output", default="ml/artifacts", help="Directory to save model")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    train(args.data, args.text_col, args.label_col, args.output, args.seed)

if __name__ == "__main__":
    main()
