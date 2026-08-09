# Resume Classifier API

A Django REST Framework API that classifies resumes into job categories using a trained LightGBM model. Upload resumes against a job circular and get ranked candidates based on classification confidence, keyword relevance, and skill matching.

## Features

- **Resume Classification** — Classifies resumes into 57 job categories using a LightGBM model (89.86% CV accuracy)
- **Multi-format Support** — Accepts PDF, DOCX, TXT files, and ZIP archives containing multiple resumes
- **Job Matching** — Ranks candidates against a job circular using a weighted scoring system
- **Skill & Experience Filtering** — Optional skill matching and minimum experience filtering
- **Top-K Ranking** — Returns the top K candidates sorted by final score

## Scoring System

Each resume is scored using three components:

| Component               | Weight | Description                                      |
|-------------------------|--------|--------------------------------------------------|
| Classification Confidence | 50%  | LightGBM model prediction confidence             |
| Job Relevance            | 30%   | Keyword overlap between resume and job circular   |
| Skill/Experience Bonus   | 20%   | Matches on required skills and experience years   |

## Tech Stack

- **Python 3.13+**
- **Django 4.2** + **Django REST Framework 3.14**
- **LightGBM** — Classification model
- **scikit-learn** — TF-IDF vectorization and feature scaling
- **joblib** — Model serialization
- **PyPDF2 / python-docx** — Resume text extraction

## Project Structure

```
├── manage.py            # Django management script
├── settings.py          # Django settings
├── urls.py              # URL routing
├── wsgi.py              # WSGI entry point
├── views.py             # API view classes
├── serializers.py       # DRF request serializers
├── model.py             # LightGBM model wrapper
├── utils.py             # File extraction & scoring utilities
├── requirements.txt     # Python dependencies
├── api/                 # Django app
│   ├── __init__.py
│   └── apps.py
├── models/              # Trained model artifacts
│   ├── best_classifier.pkl
│   ├── tfidf_vectorizer.pkl
│   ├── scaler.pkl
│   └── model_metadata.json
└── data/                # Working data directory
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/cvjachai.git
cd cvjachai
```

### 2. Create a virtual environment

```bash
python -m venv tf_env
# Windows
tf_env\Scripts\activate
# macOS/Linux
source tf_env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add model files

Place the trained model artifacts in the `models/` directory:

- `best_classifier.pkl`
- `tfidf_vectorizer.pkl`
- `scaler.pkl`
- `model_metadata.json`

> **Note:** Model `.pkl` files are excluded from version control via `.gitignore` due to their size. You'll need to obtain them separately or train your own model.

### 5. Run the server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

### `GET /api/`

Returns API information and available categories.

### `GET /api/health`

Health check — returns server status and model info.

### `GET /api/categories`

Lists all 57 supported job categories.

### `POST /api/classify`

Classify and rank resumes against a job circular.

**Content-Type:** `multipart/form-data`

| Parameter       | Type     | Required | Description                                  |
|-----------------|----------|----------|----------------------------------------------|
| `job_circular`  | string   | Yes      | Job description text                         |
| `resume_files`  | file(s)  | Yes      | Resume files (PDF, DOCX, TXT, or ZIP)        |
| `top_k`         | integer  | No       | Number of top candidates to return (default 5)|
| `skills`        | string   | No       | Comma-separated required skills              |
| `min_experience`| integer  | No       | Minimum years of experience                  |

**Example using cURL:**

```bash
curl -X POST http://127.0.0.1:8000/api/classify \
  -F "job_circular=Looking for a Python developer with 3 years experience in Django and REST APIs" \
  -F "resume_files=@resume1.pdf" \
  -F "resume_files=@resume2.docx" \
  -F "top_k=3" \
  -F "skills=python,django,rest api" \
  -F "min_experience=3"
```

**Example Response:**

```json
{
  "job_circular_preview": "Looking for a Python developer with 3 years experience...",
  "skills_searched": ["python", "django", "rest api"],
  "min_experience": 3,
  "total_resumes": 2,
  "processed_resumes": 2,
  "top_k": 3,
  "ranked_resumes": [
    {
      "filename": "resume1.pdf",
      "predicted_category": "python-developer",
      "confidence": 0.9234,
      "job_relevance": 0.7521,
      "skill_bonus": 0.65,
      "final_score": 0.8173,
      "top_categories": {
        "python-developer": 0.9234,
        "data-science-engineer": 0.0312,
        "devops-engineer": 0.0156
      }
    }
  ]
}
```

## Model Details

- **Algorithm:** LightGBM Classifier
- **Cross-validation Accuracy:** 89.86%
- **Feature Vector:** 921 dimensions
  - 200 TF-IDF features
  - 717 binary skill features
  - 4 text statistics (char count, word count, avg word length, unique word ratio)
- **Categories:** 57 job categories

## License

This project is for educational and research purposes.
