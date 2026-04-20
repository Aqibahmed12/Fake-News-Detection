"""
ML Engine — Model loading, inference, and explainability.
Supports 'logistic' (default) and 'xgboost' model types.
"""
import os
import time
import json
import numpy as np
from typing import Dict, Any, Optional, List

# Import feature names from the single source of truth
from app.services.nlp_pipeline import NUMERIC_FEATURE_NAMES

# Label thresholds (score 0–1, higher = more credible)
LABEL_THRESHOLDS = [
    (0.80, "REAL"),
    (0.60, "LIKELY_REAL"),
    (0.40, "UNCERTAIN"),
    (0.20, "LIKELY_FAKE"),
    (0.00, "FAKE"),
]

LABEL_COLORS = {
    "REAL": "#22c55e",
    "LIKELY_REAL": "#86efac",
    "UNCERTAIN": "#facc15",
    "LIKELY_FAKE": "#f97316",
    "FAKE": "#ef4444",
}


def score_to_label(score: float) -> str:
    for threshold, label in LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "FAKE"


class MLEngine:
    """Loads and runs ML models for fake news detection."""

    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self._logistic = None
        self._xgboost = None
        self._tfidf = None
        self._scaler = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Model persistence paths
    # ------------------------------------------------------------------

    def _path(self, name: str) -> str:
        return os.path.join(self.models_dir, name)

    def is_trained(self) -> bool:
        return (
            os.path.exists(self._path("tfidf.pkl"))
            and os.path.exists(self._path("logistic.pkl"))
        )

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _load(self):
        if self._loaded:
            return
        import joblib
        if not self.is_trained():
            raise RuntimeError("No trained model found. Run train_model.py first.")
        self._tfidf = joblib.load(self._path("tfidf.pkl"))
        self._scaler = joblib.load(self._path("scaler.pkl"))
        self._logistic = joblib.load(self._path("logistic.pkl"))
        if os.path.exists(self._path("xgboost.pkl")):
            self._xgboost = joblib.load(self._path("xgboost.pkl"))
        self._loaded = True

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(
        self,
        text: str,
        model_type: str = "logistic",
        return_features: bool = False,
    ) -> Dict[str, Any]:
        """
        Run inference on a single text.
        Returns: {score, label, confidence, features, processing_ms}
        """
        from app.services.nlp_pipeline import preprocess

        start = time.monotonic()
        self._load()

        processed = preprocess(text)
        cleaned = processed["lemmatised_text"] or processed["cleaned_text"] or text

        # TF-IDF vector
        tfidf_vec = self._tfidf.transform([cleaned])

        # Numeric features
        num_feats = np.array(
            [processed["numeric_features"].get(f, 0.0) for f in NUMERIC_FEATURE_NAMES],
            dtype=np.float32,
        ).reshape(1, -1)
        num_feats_scaled = self._scaler.transform(num_feats)

        # Choose model
        from scipy.sparse import hstack, csr_matrix
        X = hstack([tfidf_vec, csr_matrix(num_feats_scaled)])

        if model_type == "xgboost" and self._xgboost is not None:
            model = self._xgboost
        else:
            model = self._logistic

        proba = model.predict_proba(X)[0]
        # Class 1 = REAL (credible)
        if len(proba) == 2:
            score = float(proba[1])
            confidence = float(max(proba))
        else:
            score = float(proba[-1])
            confidence = float(max(proba))

        label = score_to_label(score)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        result: Dict[str, Any] = {
            "score": round(score, 4),
            "label": label,
            "confidence": round(confidence, 4),
            "processing_ms": elapsed_ms,
            "model_used": model_type,
        }

        if return_features:
            result["features"] = self._top_features(
                processed["numeric_features"],
                processed["cleaned_text"],
                score,
                label,
            )

        return result

    def _top_features(
        self,
        numeric_features: Dict[str, float],
        cleaned_text: str,
        score: float,
        label: str,
    ) -> List[Dict[str, Any]]:
        """Build human-readable top contributing features."""
        explanations = []

        # Sentiment
        sent = numeric_features.get("sentiment_compound", 0)
        if abs(sent) > 0.3:
            explanations.append({
                "feature": "Sentiment",
                "value": f"{sent:+.2f}",
                "impact": "negative" if sent < -0.3 else "positive",
                "description": "Highly negative tone detected" if sent < -0.3
                               else "Positive/neutral tone detected",
            })

        # Sensational words
        sens = numeric_features.get("sensational_word_count", 0)
        if sens > 0:
            explanations.append({
                "feature": "Sensational Language",
                "value": str(int(sens)),
                "impact": "negative",
                "description": f"{int(sens)} sensational/clickbait word(s) found",
            })

        # ALL-CAPS words
        caps = numeric_features.get("caps_word_ratio", 0)
        if caps > 0.05:
            explanations.append({
                "feature": "Excessive Capitalization",
                "value": f"{caps*100:.1f}%",
                "impact": "negative",
                "description": "Unusually high ratio of ALL-CAPS words",
            })

        # Exclamation marks
        exc = numeric_features.get("exclamation_ratio", 0)
        if exc > 0.02:
            explanations.append({
                "feature": "Exclamation Marks",
                "value": f"{exc*100:.1f}% of words",
                "impact": "negative",
                "description": "Excessive use of exclamation marks",
            })

        # Readability
        fk = numeric_features.get("flesch_kincaid", 12)
        explanations.append({
            "feature": "Readability (FK Grade)",
            "value": f"{fk:.1f}",
            "impact": "positive" if 6 <= fk <= 14 else "neutral",
            "description": f"Flesch-Kincaid grade level {fk:.1f} "
                           f"({'appropriate' if 6 <= fk <= 14 else 'unusual'} complexity)",
        })

        # Entity density
        ent = numeric_features.get("entity_density", 0)
        explanations.append({
            "feature": "Named Entity Density",
            "value": f"{ent*100:.1f}%",
            "impact": "positive" if ent > 0.03 else "neutral",
            "description": "Named entities (persons, orgs, locations) found"
                           if ent > 0.03 else "Few named entities found",
        })

        return explanations[:5]

    def health(self) -> Dict[str, Any]:
        return {
            "trained": self.is_trained(),
            "logistic_loaded": self._logistic is not None,
            "xgboost_loaded": self._xgboost is not None,
            "models_dir": self.models_dir,
        }
