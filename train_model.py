"""
Model Training Script
Run: python train_model.py
Trains TF-IDF + Logistic Regression and XGBoost classifiers on the
bundled demo dataset (or any CSV with 'text' and 'label' columns where
label is 0=Fake, 1=Real).
"""
import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")


def train_and_save(models_dir: str, data_dir: str):
    import numpy as np
    import pandas as pd
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, f1_score
    from scipy.sparse import hstack, csr_matrix

    print("[Train] Loading dataset...")
    demo_path = os.path.join(data_dir, "demo_dataset.csv")
    if not os.path.exists(demo_path):
        raise FileNotFoundError(f"Dataset not found at {demo_path}")

    df = pd.read_csv(demo_path)
    df = df.dropna(subset=["text", "label"])
    df["label"] = df["label"].astype(int)
    print(f"[Train] Dataset: {len(df)} rows | Real: {df['label'].sum()} | Fake: {(df['label']==0).sum()}")

    # NLP preprocessing
    print("[Train] Preprocessing text...")
    from app.services.nlp_pipeline import clean_text, lemmatise, extract_features, NUMERIC_FEATURE_NAMES

    cleaned_texts = []
    numeric_matrix = []
    raw_cleaned = []

    for i, row in df.iterrows():
        text = str(row["text"])
        cleaned = clean_text(text)
        lemmed = lemmatise(cleaned)
        # Fallback: if lemmatiser ate all words, use cleaned text
        tfidf_text = lemmed.strip() if lemmed.strip() else cleaned.strip()
        cleaned_texts.append(tfidf_text)
        raw_cleaned.append(cleaned)
        feats = extract_features(text)
        numeric_matrix.append([feats.get(f, 0.0) for f in NUMERIC_FEATURE_NAMES])

        if (i + 1) % 200 == 0:
            print(f"  ... processed {i+1}/{len(df)}")

    X_num = np.array(numeric_matrix, dtype=np.float32)
    y = df["label"].values

    # TF-IDF
    print("[Train] Fitting TF-IDF vectoriser...")
    tfidf = TfidfVectorizer(
        max_features=15_000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    )
    X_tfidf = tfidf.fit_transform(cleaned_texts)

    # Scale numeric features
    scaler = StandardScaler()
    X_num_scaled = scaler.fit_transform(X_num)

    X = hstack([X_tfidf, csr_matrix(X_num_scaled)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Logistic Regression
    print("[Train] Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42)
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_f1 = f1_score(y_test, lr_preds, average="weighted")
    print(f"[Train] Logistic Regression F1: {lr_f1:.3f}")
    print(classification_report(y_test, lr_preds, target_names=["Fake", "Real"]))

    # XGBoost
    xgb_model = None
    try:
        import xgboost as xgb
        print("[Train] Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        xgb_model.fit(X_train, y_train)
        xgb_preds = xgb_model.predict(X_test)
        xgb_f1 = f1_score(y_test, xgb_preds, average="weighted")
        print(f"[Train] XGBoost F1: {xgb_f1:.3f}")
    except Exception as e:
        print(f"[Train] XGBoost skipped: {e}")

    # Save artefacts
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(tfidf, os.path.join(models_dir, "tfidf.pkl"))
    joblib.dump(scaler, os.path.join(models_dir, "scaler.pkl"))
    joblib.dump(lr, os.path.join(models_dir, "logistic.pkl"))
    if xgb_model is not None:
        joblib.dump(xgb_model, os.path.join(models_dir, "xgboost.pkl"))

    # Save metadata
    meta = {
        "logistic_f1": round(lr_f1, 4),
        "xgboost_f1": round(xgb_f1, 4) if xgb_model else None,
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "tfidf_features": tfidf.max_features,
    }
    with open(os.path.join(models_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"[Train] Saved models to {models_dir}")
    return meta


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    sys.path.insert(0, base)

    models_dir = os.path.join(base, "models_cache")
    data_dir = os.path.join(base, "data")

    train_and_save(models_dir, data_dir)
