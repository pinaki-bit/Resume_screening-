# ML Pipeline — Dataset Instructions

This directory will contain the training pipeline for the resume screening ML model.

## ⚠️ Important: Do NOT invent training data

The model must be trained only on a **real, publicly available** resume dataset
provided by the project owner. No synthetic or invented data will be used.

---

## Expected Dataset Format

Place your dataset CSV at:

```
ml/data/raw/resumes.csv
```

Required columns (minimum):

| Column | Type | Description |
|--------|------|-------------|
| `resume_text` | str | Full plain-text content of the resume |
| `category` | str | Job category / role label (e.g. "Data Scientist") |

Optional but recommended columns:
- `candidate_name`
- `years_experience`
- `skills` (comma-separated)

---

## Training Pipeline (Phase 3 — to be implemented)

Once the dataset is provided, the following files will be created:

```
ml/
├── data/
│   ├── raw/            ← place resumes.csv here
│   └── processed/      ← auto-generated preprocessed files
├── pipeline/
│   ├── preprocess.py   ← text cleaning, TF-IDF vectorisation
│   ├── train.py        ← model training (scikit-learn)
│   ├── evaluate.py     ← classification report, confusion matrix
│   └── predict.py      ← inference wrapper called by FastAPI
└── models/             ← serialised model files (.joblib)
```

### Run training (Phase 3+)

```bash
cd ml
python -m pipeline.train --data data/raw/resumes.csv --output models/
```

---

## Directory Placeholders

`ml/data/raw/` and `ml/models/` are git-ignored and must be created locally.

```bash
mkdir -p ml/data/raw ml/data/processed ml/models
```
