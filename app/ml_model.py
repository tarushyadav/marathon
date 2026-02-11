import joblib
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sqlalchemy.orm import Session

from app.db import SessionLocal, WorkerDB
from app.analytics import calculate_employability

MODEL_PATH = "employability_model.pkl"


def extract_features(worker):
    skill_score = 1 if worker.skill.lower() in ["delivery", "cleaning", "driver"] else 0
    return [
        worker.experience_years,
        skill_score,
        worker.salary
    ]


def train_from_database():
    db: Session = SessionLocal()

    try:
        workers = db.query(WorkerDB).all()

        if len(workers) < 3:
            raise Exception("Not enough data to train model")

        X = []
        y = []

        for worker in workers:
            features = extract_features(worker)
            score, _ = calculate_employability(worker)  # pseudo-label

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


def load_model():
    return joblib.load(MODEL_PATH)


def predict_score(worker):
    model = load_model()
    features = np.array([extract_features(worker)])
    score = model.predict(features)[0]
    return int(min(max(score, 1), 10))