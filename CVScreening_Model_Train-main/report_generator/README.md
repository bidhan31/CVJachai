# CV Screening — Report Generator

> **Standalone folder** — delete this entire `report_generator/` directory to remove everything cleanly.

## What's in here

| File | Purpose |
|------|---------|
| `generate_report.py` | Main script — generates the DOCX report |
| `requirements.txt` | Only dependency: `python-docx` |
| `cv_screening_report.docx` | Output file (created after running) |

## How to run

```powershell
cd "c:\My Space\Projects\cvscreening\report_generator"
pip install -r requirements.txt
python generate_report.py
```

The report will be saved as **`cv_screening_report.docx`** in this folder.

## Report Contents

1. **Cover Page** — title, date, model stats
2. **Table of Contents**
3. **Section 1 — Dataset Finalization**
   - Data sources & collection strategy
   - Category normalization mapping
   - Full category distribution table (51 categories, 8,519 samples)
   - Feature engineering pipeline
   - Dataset quality & challenges
4. **Section 2 — Algorithm / Model Selection**
   - Why ensemble approach
   - All 3 models evaluated (Random Forest, LightGBM, CatBoost)
   - Feature representation (skill vectors + TF-IDF)
   - SMOTE-inside-folds design decision
   - Final model architecture (8-step pipeline)
   - Training results table
5. **Section 3 — Comparative Analysis**
   - Dataset comparison vs 6 published works
   - Model performance comparison table
   - Feature richness comparison (13 features × 5 systems)
   - Discussion of strengths & limitations
6. **Section 4 — Conclusion & Future Work**
7. **Section 5 — References** (10 citations)

## To remove

Simply delete this folder:
```powershell
Remove-Item -Recurse -Force "c:\My Space\Projects\cvscreening\report_generator"
```
