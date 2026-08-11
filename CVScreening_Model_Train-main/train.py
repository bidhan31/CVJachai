"""
Training pipeline for Resume Screening Model
Uses TF-IDF + skill vectors + text statistics (Matches backend expectation exactly)
Models: Leaderboard comparison of elite models
"""

import numpy as np
import json
import joblib
import warnings
from pathlib import Path
from tqdm import tqdm
from collections import Counter

from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import clone as sk_clone
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression

from config import PROCESSED_DATA_DIR, MODEL_SAVE_DIR, TECHNICAL_SKILLS, SOFT_SKILLS

warnings.filterwarnings('ignore')

def load_data():
    """Load categories and raw texts."""
    cat_meta_path = PROCESSED_DATA_DIR / "categories.json"
    corpus_path = PROCESSED_DATA_DIR / "resume_raw_texts.json"
    
    if not corpus_path.exists() or not cat_meta_path.exists():
        print(f"Error: {corpus_path} or {cat_meta_path} not found. Run create_dataset.py first.")
        return None, None, None, None

    # Load categories metadata
    with open(cat_meta_path, 'r', encoding='utf-8') as f:
        cat_data = json.load(f)
        categories = cat_data.get("categories", [])
        if not categories:
            # Fallback if categories were saved incorrectly
            categories = cat_data if isinstance(cat_data, list) else list(cat_data.keys())
            
    with open(corpus_path, 'r', encoding='utf-8') as f:
        corpus_data = json.load(f)
        
    texts = []
    labels = []
    filenames = []
    
    for item in corpus_data:
        texts.append(item.get("raw_text", ""))
        cat = item.get("category", "")
        if cat in categories:
            labels.append(categories.index(cat))
        else:
            if cat not in categories:
                categories.append(cat)
            labels.append(categories.index(cat))
        filenames.append(item.get("filename", ""))
        
    labels = np.array(labels, dtype=np.int64)
    
    return texts, labels, categories, filenames

def build_features(texts, all_skills):
    """Build exact features expected by backend engine/model.py"""
    print("Building TF-IDF vectorizer (max_features=200)...")
    tfidf_vectorizer = TfidfVectorizer(max_features=200, stop_words='english')
    tfidf_features = tfidf_vectorizer.fit_transform(texts).toarray()
    
    print("Building skill and text stat features...")
    skill_features_list = []
    extra_features_list = []
    
    for text in tqdm(texts, desc="Extracting"):
        text_lower = text.lower()
        # Binary skills
        skills = [1 if s.lower() in text_lower else 0 for s in all_skills]
        skill_features_list.append(skills)
        
        # Text stats
        words = text.split()
        word_count = len(words) if words else 1
        char_count = len(text)
        avg_word_len = np.mean([len(w) for w in words]) if words else 0
        unique_word_ratio = len(set(words)) / word_count
        
        extra_features_list.append([char_count, word_count, avg_word_len, unique_word_ratio])
        
    skill_features = np.array(skill_features_list, dtype=np.float32)
    extra_features = np.array(extra_features_list, dtype=np.float32)
    
    # Combine: [TF-IDF (200)] + [Skills (717+)] + [Extra (4)]
    X_combined = np.hstack([tfidf_features, skill_features, extra_features])
    
    return X_combined, tfidf_vectorizer

def train_model():
    """Train ensemble classifier with leaderboard."""
    print("=" * 60)
    print("ULTIMATE RESUME CLASSIFIER TRAINING (TF-IDF Version)")
    print("=" * 60 + "\n")

    texts, labels, categories, filenames = load_data()
    if texts is None: return
    
    all_skills = TECHNICAL_SKILLS + SOFT_SKILLS

    X_combined, tfidf_vectorizer = build_features(texts, all_skills)
    print(f"Total features: {X_combined.shape[1]}")
    
    # Handle tiny classes for CV/SMOTE
    class_counts = Counter(labels)
    min_class_size = min(class_counts.values())
    
    if min_class_size < 2:
        print(f"Warning: Found classes with < 2 samples. Removing them for training to allow SMOTE/CV.")
        valid_indices = [i for i, label in enumerate(labels) if class_counts[label] >= 2]
        X_combined = X_combined[valid_indices]
        labels = labels[valid_indices]
        # Recompute min_class_size
        class_counts = Counter(labels)
        min_class_size = min(class_counts.values())

    # CV Setup
    n_folds = min(5, min_class_size)
    print(f"Starting {n_folds}-fold Cross-Validation...")

    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

    # Model Params
    cat_params = {'iterations': 1000, 'depth': 8, 'learning_rate': 0.05, 'verbose': 0, 'random_seed': 42}
    lgbm_params = {'n_estimators': 1000, 'learning_rate': 0.05, 'random_state': 42, 'verbose': -1}
    xgb_params = {'n_estimators': 1000, 'learning_rate': 0.05, 'random_state': 42}

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
    all_cv_results = {}
    best_std = 0.0

    print("\n" + "-" * 30)
    print("  LEADERBOARD")
    print("-" * 30)

    for name, model_template in models:
        scores = []
        with tqdm(total=n_folds, desc=f"  {name:15}", leave=False) as pbar:
            for train_idx, val_idx in cv.split(X_combined, labels):
                X_train, X_val = X_combined[train_idx], X_combined[val_idx]
                y_train, y_val = labels[train_idx], labels[val_idx]
                
                # Resample + Scale
                try:
                    sm = SMOTE(random_state=42, k_neighbors=min(5, min_class_size-1))
                    X_res, y_res = sm.fit_resample(X_train, y_train)
                except Exception as e:
                    X_res, y_res = X_train, y_train
                    
                sc = StandardScaler()
                X_res = sc.fit_transform(X_res)
                X_val = sc.transform(X_val)
                
                m = sk_clone(model_template)
                m.fit(X_res, y_res)
                scores.append(accuracy_score(y_val, m.predict(X_val)))
                pbar.update(1)
        
        avg_score = np.mean(scores)
        std_score = np.std(scores)
        all_cv_results[name] = {"mean": float(avg_score), "std": float(std_score)}
        print(f"  {name:15}: {avg_score*100:.1f}% (+/- {std_score*100:.1f}%)")
        if avg_score > best_score:
            best_score = avg_score
            best_std = std_score
            best_name = name
            best_model = model_template

    print(f"\nWINNER: {best_name} ({best_score*100:.1f}% Accuracy)")
    
    # Final training
    print(f"Training final {best_name} on all data...")
    try:
        sm = SMOTE(random_state=42, k_neighbors=min(5, min_class_size-1))
        X_res, y_res = sm.fit_resample(X_combined, labels)
    except Exception:
        X_res, y_res = X_combined, labels
        
    sc = StandardScaler()
    X_final = sc.fit_transform(X_res)
    
    final_m = sk_clone(best_model)
    final_m.fit(X_final, y_res)
    
    train_acc = accuracy_score(y_res, final_m.predict(X_final))
    
    # Save
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_m, MODEL_SAVE_DIR / "best_classifier.pkl")
    joblib.dump(sc, MODEL_SAVE_DIR / "scaler.pkl")
    joblib.dump(tfidf_vectorizer, MODEL_SAVE_DIR / "tfidf_vectorizer.pkl")
    
    metadata = {
        "best_model": best_name,
        "cv_accuracy": float(best_score),
        "cv_std": float(best_std),
        "all_cv_results": all_cv_results,
        "train_accuracy": float(train_acc),
        "categories": categories,
        "skill_list": all_skills,
        "num_skill_features": len(all_skills),
        "num_tfidf_features": len(tfidf_vectorizer.get_feature_names_out()),
        "num_text_stat_features": 4,
        "total_features": X_combined.shape[1],
        "total_samples": len(texts)
    }
    
    with open(MODEL_SAVE_DIR / "model_metadata.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSUCCESS: Model and metadata saved to {MODEL_SAVE_DIR}/")

if __name__ == "__main__":
    train_model()
