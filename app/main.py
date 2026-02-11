from fastapi import FastAPI, HTTPException
from app.schemas import   WorkerCreate, WorkerResponse
from app.db import Base, engine, SessionLocal, WorkerDB
from app.analytics import calculate_employability
from app.ml_model import predict_score
from app.score_engine import calculate_final_score
from app.schemas import WorkerScoreInput

app = FastAPI()

# Create DB tables on startup
Base.metadata.create_all(bind=engine)


# -------------------------
# CREATE WORKER
# -------------------------
@app.post("/workers", response_model=WorkerResponse, status_code=201)
def create_worker(worker: WorkerCreate):
    db = SessionLocal()
    try:
        existing = db.query(WorkerDB).filter(
            WorkerDB.email == worker.email
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already exists"
            )

        db_worker = WorkerDB(**worker.dict())
        db.add(db_worker)
        db.commit()
        db.refresh(db_worker)

        return {
            "message": "Worker created",
            "worker": db_worker
        }
    finally:
        db.close()


# -------------------------
# LIST WORKERS
# -------------------------
@app.get("/workers")
def list_workers():
    db = SessionLocal()
    try:
        return db.query(WorkerDB).all()
    finally:
        db.close()


# -------------------------
# ANALYTICS ENDPOINT
# -------------------------
@app.get("/workers/{worker_id}/analytics")
def worker_analytics(worker_id: int):
    db = SessionLocal()
    try:
        worker = db.query(WorkerDB).filter(
            WorkerDB.id == worker_id
        ).first()

        if not worker:
            raise HTTPException(
                status_code=404,
                detail="Worker not found"
            )

        score, reasons = calculate_employability(worker)

        return {
            "worker_id": worker.id,
            "employability_score": score,
            "reasons": reasons

        }
    finally:
        db.close()

# -------------------------
# COMPARE RULE-BASED VS ML SCORE
# ------------------------- 
# This endpoint allows us to see how closely the ML model's predictions align with our rule-based scoring.
# The confidence score gives us an idea of how much we can trust the ML prediction based on its agreement with the rule-based score.
def calculate_confidence(rule_score: int, ml_score: int) -> float:
    diff = abs(rule_score - ml_score)

    if diff == 0:
        return 0.90
    elif diff == 1:
        return 0.75
    elif diff == 2:
        return 0.55
    else:
        return 0.35
# The confidence thresholds are somewhat arbitrary and can be adjusted based on real-world performance and requirements.
# A smaller difference between the rule-based and ML scores indicates higher confidence in the ML prediction,
#  while a larger difference suggests lower confidence.
@app.get("/workers/{worker_id}/compare")
def compare_rule_vs_ml(worker_id: int):
    db = SessionLocal()
    try:
        worker = db.query(WorkerDB).filter(
            WorkerDB.id == worker_id
        ).first()

        if not worker:
            raise HTTPException(
                status_code=404,
                detail="Worker not found"
            )

        # Rule-based score
        rule_score, _ = calculate_employability(worker)

        # ML-based score
        ml_score = predict_score(worker)

        # Calculate confidence based on score difference
        confidence = calculate_confidence(rule_score, ml_score)

        return {
            "worker_id": worker.id,
            "rule_score": rule_score,
            "ml_score": ml_score,
            "difference": ml_score - rule_score,
            "confidence": confidence
        }

    finally:
        db.close()

# -------------------------
# SCORE DISTRIBUTION ENDPOINT
# -------------------------
# This endpoint provides a distribution of employability scores across all workers, comparing the rule-based and ML-based scores.
def empty_distribution():
    return {str(i): 0 for i in range(1, 11)}

# By analyzing the score distributions, we can identify if there are any significant discrepancies between the rule-based and ML-based scoring systems.
# For example, if the ML model consistently gives higher scores than the rule-based system,
#  it may indicate that the model is overestimating employability, or vice versa. This insight can help us refine our model and ensure it aligns well with our business goals.
@app.get("/analytics/distribution")
def score_distribution():
    db = SessionLocal()
    try:
        workers = db.query(WorkerDB).all()

        rule_dist = empty_distribution()
        ml_dist = empty_distribution()

        for worker in workers:
            rule_score, _ = calculate_employability(worker)
            ml_score = predict_score(worker)

            rule_dist[str(rule_score)] += 1
            ml_dist[str(ml_score)] += 1

        return {
            "rule_score_distribution": rule_dist,
            "ml_score_distribution": ml_dist
        }

    finally:
        db.close()

# Temporary global assumptions
GLOBAL_MEAN_RATING = 4.2
MAX_SALARY = 50000


@app.post("/score")
def score_worker(worker: WorkerScoreInput):
    final_score = calculate_final_score(
        worker,
        global_mean=GLOBAL_MEAN_RATING,
        max_salary=MAX_SALARY
    )

    return {
        "final_score": final_score
    }