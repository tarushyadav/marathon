from app.explainability import derive_adjustment_reasons
from app.ml_model import predict_worker

# ---------------- CONFIG ---------------- #

WEIGHTS = {
    "on_time": 0.25,
    "completion": 0.20,
    "rating": 0.15,
    "complaints": 0.25,
    "experience_years": 0.05,
    "salary": 0.05,
    "job_volume": 0.05
}

CONFIDENCE_M = 20
LOW_DATA_THRESHOLD = 5
ANOMALY_JOBS_PER_DAY = 20
DECAY_FACTOR = 0.8

RULE_WEIGHT = 0.6
ML_WEIGHT = 0.4


# ------------------------------------------------
# 1️⃣ SAFE FEATURE EXTRACTION (NO MUTATION)
# ------------------------------------------------
def extract_safe_values(worker, max_salary: float):

    rating = max(0, min(getattr(worker, "rating", 0) or 0, 5))
    on_time = max(0, min(getattr(worker, "on_time", 0) or 0, 100))
    completion = max(0, min(getattr(worker, "completion", 0) or 0, 100))
    experience_years = max(0, getattr(worker, "experience_years", 0) or 0)
    salary = max(0, getattr(worker, "salary", 0) or 0)
    complaints = max(0, getattr(worker, "complaints", 0) or 0)
    jobs_completed = max(0, getattr(worker, "jobs_completed", 0) or 0)

    max_salary = max(max_salary, 1)

    return (
        rating,
        on_time,
        completion,
        experience_years,
        salary,
        complaints,
        jobs_completed,
        max_salary
    )


# ------------------------------------------------
# 2️⃣ NORMALIZATION
# ------------------------------------------------
def normalize_features(worker, max_salary: float):

    (
        rating,
        on_time,
        completion,
        experience_years,
        salary,
        complaints,
        jobs_completed,
        max_salary
    ) = extract_safe_values(worker, max_salary)

    rating_norm = rating / 5
    on_time_norm = (on_time / 100) ** 2
    completion_norm = (completion / 100) ** 2
    experience_norm = min(experience_years / 5, 1)

    salary_norm = max(0, 1 - (salary / max_salary))
    complaint_norm = 1 / (1 + complaints)
    job_volume_norm = min(jobs_completed / 50, 1)

    return {
        "rating": rating_norm,
        "on_time": on_time_norm,
        "completion": completion_norm,
        "experience_years": experience_norm,
        "salary": salary_norm,
        "complaints": complaint_norm,
        "job_volume": job_volume_norm
    }


# ------------------------------------------------
# 3️⃣ RULE-BASED SCORE
# ------------------------------------------------
def calculate_rule_score(worker, max_salary: float):

    normalized = normalize_features(worker, max_salary)

    score = 0
    for key, weight in WEIGHTS.items():
        score += normalized[key] * weight

    return score * 10


# ------------------------------------------------
# 4️⃣ BAYESIAN RATING
# ------------------------------------------------
def calculate_bayesian_rating(worker, global_mean: float):

    jobs_completed = max(0, getattr(worker, "jobs_completed", 0) or 0)
    rating = max(0, min(getattr(worker, "rating", 0) or 0, 5))

    adjusted_rating = (
        (global_mean * CONFIDENCE_M + rating * jobs_completed)
        / (CONFIDENCE_M + jobs_completed)
    )

    return (adjusted_rating / 5) * 10


# ------------------------------------------------
# 5️⃣ FINAL SCORE WITH ML + EDGE CASES
# ------------------------------------------------
def calculate_final_score(worker, global_mean: float, max_salary: float):

    # ----- RULE SCORE -----
    rule_score = calculate_rule_score(worker, max_salary)
    bayesian_score = calculate_bayesian_rating(worker, global_mean)

    blended_rule_score = (0.8 * rule_score) + (0.2 * bayesian_score)

    # ----- ML PREDICTION -----
    ml_output = predict_worker(worker)

    ml_score = ml_output["predicted_quality"] * 10
    ml_confidence = ml_output["confidence"]

    # ----- HYBRID BLENDING (FIXED LOGIC) -----
    hybrid_score = (
        RULE_WEIGHT * blended_rule_score +
        ML_WEIGHT * (ml_score * ml_confidence)
    )

    final_score = hybrid_score

    jobs_completed = max(0, getattr(worker, "jobs_completed", 0) or 0)

    # ------------------------------------------------
    # EDGE CASE 1: Low Data Cap
    # ------------------------------------------------
    if jobs_completed < LOW_DATA_THRESHOLD:
        final_score = min(max(final_score, 4.0), 7.0)

    # ------------------------------------------------
    # EDGE CASE 2: Zero Activity Decay
    # ------------------------------------------------
    if jobs_completed == 0:
        final_score *= DECAY_FACTOR

    # ------------------------------------------------
    # EDGE CASE 3: Activity Anomaly Dampening
    # ------------------------------------------------
    active_days = getattr(worker, "active_days", 0) or 0

    if active_days > 0:
        jobs_per_day = jobs_completed / max(active_days, 1)
        if jobs_per_day > ANOMALY_JOBS_PER_DAY:
            final_score *= 0.85

    # ------------------------------------------------
    # FINAL SAFETY CLAMP
    # ------------------------------------------------
    final_score = max(0, min(final_score, 10))

    explanation = {
        "rule_score": round(rule_score, 2),
        "bayesian_score": round(bayesian_score, 2),
        "ml_score": round(ml_score, 2),
        "ml_confidence": round(ml_confidence, 2),
        "hybrid_before_edge_cases": round(hybrid_score, 2),
        "final_score": round(final_score, 2),
        "reasons": derive_adjustment_reasons(worker)
    }

    return round(final_score, 2), explanation