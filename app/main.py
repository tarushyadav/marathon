from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.schemas import WorkerCreate, WorkerResponse, WorkerScoreInput
from app.db import Base, engine, SessionLocal, WorkerDB
from app.analytics import calculate_employability
from app.ml_model import predict_worker
from app.score_engine import calculate_final_score
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, authenticate_admin
from app.auth import verify_token
from fastapi import Depends
from app.ml_model import train_from_database
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi import Request

# ---------------- CONFIG ---------------- #

GLOBAL_MEAN_RATING = 4.2
MAX_SALARY = 50000

# ---------------- APP INIT ---------------- #

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)# Apply rate limit to all routes
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# ---------------- DB DEPENDENCY ---------------- #

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- CREATE WORKER ---------------- #

@app.post("/workers", response_model=WorkerResponse, status_code=201)
def create_worker(worker: WorkerCreate, db: Session = Depends(get_db)):

    existing = db.query(WorkerDB).filter(
        WorkerDB.email == worker.email
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    db_worker = WorkerDB(**worker.dict())
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    return {
        "message": "Worker created",
        "worker": db_worker
    }


# ---------------- LIST WORKERS ---------------- #

@app.get("/workers")
def list_workers(
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):
    return db.query(WorkerDB).all()


# ---------------- ANALYTICS ---------------- #

@app.get("/workers/{worker_id}/analytics")
def worker_analytics(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):

    worker = db.query(WorkerDB).filter(
        WorkerDB.id == worker_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    score, reasons = calculate_employability(worker)

    return {
        "worker_id": worker.id,
        "employability_score": score,
        "reasons": reasons
    }


# ---------------- RULE VS ML COMPARISON ---------------- #

@app.get("/workers/{worker_id}/compare")
def compare_rule_vs_ml(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(verify_token)
):

    worker = db.query(WorkerDB).filter(
        WorkerDB.id == worker_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    rule_score, _ = calculate_employability(worker)
    ml_output = predict_worker(worker)

    ml_score = round(ml_output["predicted_quality"] * 10, 2)
    ml_confidence = ml_output["confidence"]

    difference = round(ml_score - rule_score, 2)

    jobs_factor = min(worker.jobs_completed / 50, 1)
    agreement_score = max(0, 1 - (abs(difference) / 10))

    confidence = round(
        0.5 * agreement_score +
        0.5 * jobs_factor,
        2
)
    return {
        "worker_id": worker.id,
        "rule_score": rule_score,
        "ml_score": ml_score,
        "ml_confidence": ml_confidence,
        "difference": difference,
        "confidence": confidence
    } 


# ---------------- SCORE DISTRIBUTION ---------------- #

def empty_distribution():
    return {str(i): 0 for i in range(1, 11)}


@app.get("/analytics/distribution")
def score_distribution(db: Session = Depends(get_db)):

    workers = db.query(WorkerDB).all()

    rule_dist = empty_distribution()
    ml_dist = empty_distribution()

    for worker in workers:
        rule_score, _ = calculate_employability(worker)
        ml_score = predict_worker(worker)

        rule_bucket = str(min(max(round(rule_score), 1), 10))
        ml_bucket = str(min(max(round(ml_score), 1), 10))

        rule_dist[rule_bucket] += 1
        ml_dist[ml_bucket] += 1

    return {
        "rule_score_distribution": rule_dist,
        "ml_score_distribution": ml_dist
    }


# ---------------- HYBRID FINAL SCORE ---------------- #

@app.post("/score")
@limiter.limit("10/minute")# Apply rate limit to this endpoint
def score_worker(request: Request, worker: WorkerScoreInput):

    final_score, explanation = calculate_final_score(
        worker,
        global_mean=GLOBAL_MEAN_RATING,
        max_salary=MAX_SALARY
    )

    return {
        "final_score": final_score,
        "details": explanation
    }


# ---------------- ADMIN RETRAIN ---------------- #

@app.post("/retrain")
@limiter.limit("2/minute")
def retrain(request: Request, user=Depends(verify_token)):

    # 👑 Role enforcement
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        train_from_database()
        return {"message": "Model retrained successfully"}
    except Exception:
        raise HTTPException(status_code=500, detail="Retraining failed")

# ---------------- ADMIN LOGIN ---------------- #

@app.post("/login")
@limiter.limit("5/minute")# Apply rate limit to login endpoint
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_admin(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ---------------- RATE LIMIT HANDLER ---------------- #

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )