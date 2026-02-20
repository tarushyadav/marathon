import joblib
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sqlalchemy.orm import Session

from app.db import SessionLocal, WorkerDB
from app.analytics import calculate_employability

MODEL_PATH = "employability_model.pkl"

_model = None  # global cached model


# -----------------------------
# FEATURE EXTRACTION
# -----------------------------
def extract_features(worker):

    skill = getattr(worker, "skill", None)

    skill_score = 1 if skill and skill.lower() in ["delivery", "cleaning", "driver"] else 0

    return [
        getattr(worker, "experience_years", getattr(worker, "experience", 0)) or 0,
        skill_score,
        getattr(worker, "salary", 0) or 0,
        getattr(worker, "rating", 0) or 0,
        getattr(worker, "jobs_completed", 0) or 0,
        getattr(worker, "complaints", 0) or 0
    ]

# -----------------------------
# TRAIN MODEL
# -----------------------------
def train_from_database():

    db: Session = SessionLocal()

    try:
        workers = db.query(WorkerDB).all()

        if len(workers) < 5:
            raise Exception("Not enough data to train model")

        X = []
        y = []

        for worker in workers:
            features = extract_features(worker)
            score, _ = calculate_employability(worker)

            X.append(features)
            y.append(score)

        X = np.array(X)
        y = np.array(y)

        model = DecisionTreeRegressor(max_depth=4)
        model.fit(X, y)

        joblib.dump(model, MODEL_PATH)

        print(f"Model retrained using {len(workers)} workers")

    finally:
        db.close()


# -----------------------------
# LOAD MODEL (CACHED)
# -----------------------------
def load_model():
    global _model

    if _model is None:
        _model = joblib.load(MODEL_PATH)

    return _model


# -----------------------------
# PREDICT WITH CONFIDENCE
# -----------------------------
def predict_worker(worker):

    model = load_model()

    features = np.array([extract_features(worker)])

    raw_score = model.predict(features)[0]

    # clamp score
    raw_score = min(max(raw_score, 1), 10)

    # normalize to 0–1 scale
    predicted_quality = raw_score / 10

    # simple confidence metric
    confidence = min((worker.jobs_completed or 0) / 50, 1)

    return {
        "predicted_quality": predicted_quality,
        "confidence": confidence
    }