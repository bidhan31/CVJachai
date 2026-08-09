"""
Training pipeline for Resume Screening Model
Uses skill vectors + SBERT semantic features
Models: Leaderboard comparison of 8 elite models
"""

import numpy as np
import json
import joblib
import warnings
import torch
from tqdm import tqdm
from collections import Counter
from pathlib import Path

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.base import clone as sk_clone
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import classification_report, accuracy_score
from sentence_transformers import SentenceTransformer
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression

from config import PROCESSED_DATA_DIR, MODEL_SAVE_DIR, TECHNICAL_SKILLS, SOFT_SKILLS

def load_data():
    """Load skill vectors + raw text."""
    csv_path = PROCESSED_DATA_DIR / "resume_skill_vectors.csv"
    json_path = PROCESSED_DATA_DIR / "resume_features.json"
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found. Run create_dataset.py first.")
        return None, None, None, None

    # Load categories metadata
    cat_meta_path = PROCESSED_DATA_DIR / "categories.json"
    with open(cat_meta_path, 'r') as f:
        categories = json.load(f)

    # Load skill vectors
    features = []
    labels = []
    filenames = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            filenames.append(row['filename'])
            labels.append(categories.index(row['category']))
            feature_vec = [float(row[skill]) for skill in reader.fieldnames if skill not in ['filename', 'category']]
            features.append(feature_vec)

    features = np.array(features, dtype=np.float32)
    labels = np.array(labels, dtype=np.int64)

    # Load raw text
    corpus_path = PROCESSED_DATA_DIR / "resume_raw_texts.json"
    if corpus_path.exists():
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
        text_map = {item['filename']: item['raw_text'] for item in corpus_data}
        texts = [text_map.get(fname, "") for fname in filenames]
    else:
        print("Warning: raw text not found, using skills as fallback.")
        texts = [" ".join([s for s in row if s]) for row in features] # Not ideal

    return features, labels, texts, categories

def train_model():
    """Train ensemble classifier with leaderboard."""
    print("=" * 60)
    print("ULTIMATE RESUME CLASSIFIER TRAINING")
    print("=" * 60 + "\n")

    features, labels, texts, categories = load_data()
    if features is None: return

    # SBERT Semantic Features
    print(f"Building SBERT features (all-mpnet-base-v2) for {len(texts)} samples...")
    sbert_model = SentenceTransformer('all-mpnet-base-v2')
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    sbert_model.to(device)
    
    sbert_embeddings = sbert_model.encode(texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True)
    X_combined = np.hstack([features, sbert_embeddings])
    print(f"Total features: {X_combined.shape[1]}")

    # CV Setup
    min_class_size = min(Counter(labels).values())
    n_folds = min(5, min_class_size)
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    print(f"Starting {n_folds}-fold Cross-Validation...")

    has_gpu = torch.cuda.is_available()

    # Model Params
    cat_params = {'iterations': 1000, 'depth': 8, 'learning_rate': 0.05, 'verbose': 0, 'random_seed': 42}
    if has_gpu: cat_params.update({'task_type': 'GPU', 'devices': '0'})

    lgbm_params = {'n_estimators': 1000, 'learning_rate': 0.05, 'random_state': 42, 'verbose': -1}
    if has_gpu: lgbm_params['device'] = 'gpu'

    xgb_params = {'n_estimators': 1000, 'learning_rate': 0.05, 'random_state': 42, 'tree_method': 'hist'}
    if has_gpu: xgb_params['device'] = 'cuda'

    models = [
        ("Random Forest", RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)),
        ("Extra Trees", ExtraTreesClassifier(n_estimators=200, class_weight='balanced', random_state=42)),
        ("CatBoost", CatBoostClassifier(**cat_params)),
        ("LightGBM", LGBMClassifier(**lgbm_params)),
        ("XGBoost", XGBClassifier(**xgb_params)),
        ("SVM", SVC(kernel='rbf', probability=True, class_weight='balanced', random_state=42)),
        ("Neural Net", MLPClassifier(hidden_layer_sizes=(512, 256), max_iter=500, random_state=42)),
        ("Logistic", LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42))
    ]

    best_score = -1.0
    best_name = ""
    best_model = None

    print("\n" + "-" * 30)
    print("  LEADERBOARD")
    print("-" * 30)

    for name, model_template in models:
        scores = []
        with tqdm(total=n_folds, desc=f"  {name}", leave=False) as pbar:
            for train_idx, val_idx in cv.split(X_combined, labels):
                X_train, X_val = X_combined[train_idx], X_combined[val_idx]
                y_train, y_val = labels[train_idx], labels[val_idx]
                
                # Resample + Scale
                sm = SMOTE(random_state=42)
                X_res, y_res = sm.fit_resample(X_train, y_train)
                sc = StandardScaler()
                X_res = sc.fit_transform(X_res)
                X_val = sc.transform(X_val)
                
                m = sk_clone(model_template)
                m.fit(X_res, y_res)
                scores.append(accuracy_score(y_val, m.predict(X_val)))
                pbar.update(1)
        
        avg_score = np.mean(scores)
        print(f"  {name:15}: {avg_score*100:.1f}%")
        if avg_score > best_score:
            best_score = avg_score
            best_name = name
            best_model = model_template

    print(f"\nWINNER: {best_name} ({best_score*100:.1f}% Accuracy)")
    
    # Final training
    print(f"Training final {best_name} on all data...")
    sm = SMOTE(random_state=42)
    X_res, y_res = sm.fit_resample(X_combined, labels)
    sc = StandardScaler()
    X_final = sc.fit_transform(X_res)
    
    final_m = sk_clone(best_model)
    final_m.fit(X_final, y_res)
    
    # Save
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_m, MODEL_SAVE_DIR / "best_classifier.pkl")
    joblib.dump(sc, MODEL_SAVE_DIR / "scaler.pkl")
    
    metadata = {
        "model_name": best_name,
        "accuracy": best_score,
        "categories": categories,
        "semantic_model": "all-mpnet-base-v2"
    }
    with open(MODEL_SAVE_DIR / "model_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\nSUCCESS: Model saved to models/ directory.")

if __name__ == "__main__":
    train_model()
