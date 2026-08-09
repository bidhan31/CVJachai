"""
Model loading and prediction module for LightGBM classifier.
"""

import json
import logging
import os
from typing import Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)


class ResumeClassifier:
    """Wrapper class for LightGBM resume classification model."""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        self.model: Any = None
        self.tfidf_vectorizer: Any = None
        self.scaler: Any = None
        self.categories: list[str] = []
        self.skill_list: list[str] = []
        self.model_metadata: dict = {}
        self.ready = False
        
        try:
            self._load_model()
            self._load_metadata()
            self.ready = True
        except (FileNotFoundError, Exception) as e:
            logger.warning(f"Model artifacts not found or could not be loaded: {e}. "
                          "The classifier will operate in fallback mode (LLM only).")
    
    def _load_model(self):
        """Load the trained LightGBM model and preprocessing objects."""
        logger.info("Loading model artifacts...")
        self.model = joblib.load(os.path.join(self.model_dir, "best_classifier.pkl"))
        self.tfidf_vectorizer = joblib.load(os.path.join(self.model_dir, "tfidf_vectorizer.pkl"))
        self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.pkl"))
        logger.info("Model loaded successfully!")
    
    def _load_metadata(self):
        """Load model metadata including categories and skill list."""
        with open(os.path.join(self.model_dir, "model_metadata.json"), 'r') as f:
            self.model_metadata = json.load(f)
        self.categories = self.model_metadata.get('categories', [])
        self.skill_list = self.model_metadata.get('skill_list', [])
        logger.info("Loaded %d categories, %d skills", len(self.categories), len(self.skill_list))
    
    def _build_features(self, resume_text: str) -> np.ndarray:
        """
        Build the full 1321-feature vector (as specified in metadata):
          - 600 TF-IDF features
          - 717 binary skill features
          - 4 text statistic features (char_count, word_count, avg_word_len, unique_word_ratio)
        """
        # TF-IDF (200 features)
        tfidf_vec = self.tfidf_vectorizer.transform([resume_text]).toarray()
        
        # Binary skill features (717 features)
        text_lower = resume_text.lower()
        skill_features = np.array([[1 if s.lower() in text_lower else 0 for s in self.skill_list]])
        
        # Text statistics (4 features)
        words = resume_text.split()
        word_count = len(words) if words else 1
        extra = np.array([[
            len(resume_text),                                    # char_count
            word_count,                                          # word_count
            np.mean([len(w) for w in words]) if words else 0,   # avg_word_len
            len(set(words)) / word_count,                        # unique_word_ratio
        ]])
        
        return np.hstack([tfidf_vec, skill_features, extra])
    
    def predict(self, resume_text: str) -> dict:
        """Predict job category for a single resume."""
        if not self.ready:
            return {
                "predicted_category": "Unknown (Model missing)",
                "confidence": 0.0,
                "all_predictions": {},
                "status": "error",
                "message": "Local ML model not found. Using fallback analysis."
            }
        
        features = self._build_features(resume_text)
        scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(scaled)[0]
        probabilities = self.model.predict_proba(scaled)[0]
        
        all_preds = {
            self.categories[i]: float(p)
            for i, p in enumerate(probabilities)
        }
        all_preds = dict(sorted(all_preds.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "predicted_category": self.categories[prediction],
            "confidence": float(probabilities[prediction]),
            "all_predictions": all_preds,
        }
    
    def predict_batch(self, resume_texts: dict[str, str]) -> dict[str, dict]:
        """Predict categories for multiple resumes."""
        return {fn: self.predict(text) for fn, text in resume_texts.items()}
    
    def get_model_info(self) -> dict:
        """Return information about the loaded model."""
        return {
            "model_type": "CatBoost Classifier",
            "best_model": self.model_metadata.get('best_model'),
            "cv_accuracy": round(self.model_metadata.get('cv_accuracy', 0), 4),
            "train_accuracy": round(self.model_metadata.get('train_accuracy', 0), 4),
            "num_categories": len(self.categories),
            "categories_sample": self.categories[:5],
        }
    
    def get_categories(self) -> list[str]:
        """Return list of all job categories."""
        return self.categories


def create_classifier(model_dir: str = "models") -> ResumeClassifier:
    return ResumeClassifier(model_dir=model_dir)
