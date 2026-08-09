# Resume Screening System

An ML-powered Applicant Tracking System (ATS) that automatically classifies resumes into job categories, scores candidates against job requirements, and makes screening decisions (SHORTLIST / REVIEW / REJECT).

## Features

- **Dynamic Category Discovery** — categories are inferred from your data, not hardcoded. Drop resumes into `dataset/<Category>/` and the system learns automatically.
- **Multi-Model Ensemble** — trains Random Forest, CatBoost, and LightGBM; auto-selects the best performer via stratified cross-validation.
- **SMOTE Balancing** — handles class imbalance by applying SMOTE inside each CV fold (no data leakage).
- **TF-IDF + Skill Vectors** — combines one-hot skill features with TF-IDF text features for robust classification.
- **Full ATS Screening Pipeline**:
  - Skill matching (required & preferred)
  - Experience & education scoring
  - Seniority detection (entry → executive)
  - Employment gap detection
  - Resume quality scoring (0–100)
  - Red flag detection (job hopping, missing contact info, etc.)
  - Knockout criteria (auto-reject on hard filters)
- **Job Description Parser** — pass free-text JDs and the engine extracts structured requirements automatically.
- **Candidate Ranking** — rank and compare multiple resumes for a single position.
- **Multi-Format Support** — PDF, DOCX, TXT, and image-based resumes (via Tesseract OCR), with best-effort extraction for legacy DOC files.
- **GPU Acceleration** — automatic GPU detection for CatBoost and LightGBM training.

## Project Structure

```
├── config.py               # All configuration, skill lists, thresholds
├── feature_extractor.py    # Resume parsing & feature extraction
├── create_dataset.py       # Build training dataset from raw resumes / CSVs
├── train.py                # Train & evaluate models (RF, CatBoost, LightGBM)
├── inference.py            # Production ATS screening engine
├── requirements.txt        # Python dependencies
├── dataset/                # Your raw resume data (organized by category)
├── processed_data/         # Generated feature CSVs & JSON (auto-created)
└── models/                 # Saved models & metadata (auto-created)
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **OCR support (optional):** Install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) if you need to process image-based resumes. The system auto-detects the Tesseract binary on your PATH or at the default Windows install location.

### 2. Prepare Your Data

Place resume files into category folders:

```
dataset/
├── software-engineer/
│   ├── resume1.pdf
│   └── resume2.docx
├── data-scientist/
│   └── resume3.pdf
├── accountant/
│   └── resume4.pdf
└── resumes.csv            # Or provide a CSV with a category/position column
```

**CSV format:** The system auto-detects category columns (`category`, `job_position_name`, `position`, etc.) and raw text columns (`resume_str`, `resume_text`, etc.). If no text column is found, it reconstructs text from structured fields (skills, education, experience).

### 3. Build the Dataset

```bash
python create_dataset.py
```

This scans everything inside `dataset/`, extracts features, deduplicates by content hash, and writes:
- `processed_data/resume_skill_vectors.csv` — one-hot skill vectors for training
- `processed_data/resume_dataset.csv` — human-readable feature table
- `processed_data/resume_features.json` — full extracted features
- `processed_data/resume_raw_texts.json` — raw text corpus for TF-IDF
- `processed_data/categories.json` — discovered categories & counts

### 4. Train the Model

```bash
python train.py
```

Trains three models with 5-fold stratified CV (SMOTE applied per fold), picks the best, retrains on all data, and saves:
- `models/best_classifier.pkl`
- `models/scaler.pkl`
- `models/tfidf_vectorizer.pkl`
- `models/model_metadata.json`

### 5. Screen Resumes

```python
from inference import ResumeScreeningEngine

engine = ResumeScreeningEngine()

# Define job requirements (or parse from a JD)
job = {
    "required_skills": ["python", "machine learning", "sql"],
    "preferred_skills": ["tensorflow", "docker", "aws"],
    "min_experience": 3,
    "max_experience": 10,
    "education_level": "bachelors",
    "seniority": "mid",
}

# Screen a single resume
result = engine.screen_resume(resume_text, job)
engine.print_screening_result(result)

# Or screen a file directly
result = engine.screen_resume_file("path/to/resume.pdf", job)

# Parse a free-text job description into structured requirements
parsed_job = engine.parse_job_description(jd_text)
result = engine.screen_resume(resume_text, parsed_job)

# Rank multiple candidates
ranked = engine.rank_resume_files(["cv1.pdf", "cv2.pdf", "cv3.pdf"], job)
```

## Screening Output

Each screened resume returns:

| Field | Description |
|---|---|
| `overall_score` | Weighted score (0–100%) |
| `decision` | `SHORTLIST` / `REVIEW` / `REJECT` |
| `decision_reason` | Human-readable explanation |
| `knockouts` | Instant-reject reasons (if any) |
| `breakdown` | Per-factor scores (skills, experience, education, etc.) |
| `candidate` | Name, email, phone, experience, education, seniority |
| `skills` | Matched/missing required & preferred skills |
| `red_flags` | Job hopping, employment gaps, missing contact info, etc. |

## Configuration

All thresholds, skill lists, and scoring weights are in [config.py](config.py):

- **`SCREENING_THRESHOLDS`** — score cutoffs for SHORTLIST (≥70), REVIEW (≥50), REJECT (<50)
- **`SCORING_WEIGHTS`** — how much each factor contributes to the overall score
- **`KNOCKOUT_CRITERIA`** — hard filters that trigger auto-reject
- **`TECHNICAL_SKILLS`** / **`SOFT_SKILLS`** — comprehensive keyword lists (500+ skills)
- **`SENIORITY_LEVELS`** — title keywords & experience thresholds per level
- **`QUALITY_CRITERIA`** — what makes a complete, professional resume

## Requirements

- Python 3.9+
- scikit-learn, CatBoost, LightGBM, imbalanced-learn
- PyPDF2, python-docx, Pillow
- Tesseract OCR (optional, for image-based resumes)

## License

MIT
