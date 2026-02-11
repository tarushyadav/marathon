# score_engine.py

from typing import List

# ---- CONFIG ----
WEIGHTS = {
    "on_time": 0.25,
    "completion": 0.20,
    "rating": 0.15,
    "complaints": 0.25,
    "experience": 0.05,
    "salary": 0.05,
    "job_volume": 0.05
}

CONFIDENCE_M = 20  # Bayesian confidence factor


# ---- NORMALIZATION ----
def normalize_features(worker, max_salary: float):
    rating_norm = worker.rating / 5
    on_time_norm = (worker.on_time / 100) ** 2
    completion_norm = (worker.completion / 100) ** 2
    experience_norm = min(worker.experience / 5, 1)
    salary_norm = 1 - (worker.salary / max_salary)
    complaint_norm = 1 / (1 + worker.complaints)
    job_volume_norm = min(worker.jobs_completed / 50, 1)

    return {
        "rating": rating_norm,
        "on_time": on_time_norm,
        "completion": completion_norm,
        "experience": experience_norm,
        "salary": salary_norm,
        "complaints": complaint_norm,
        "job_volume": job_volume_norm
    }


# ---- BASE SCORE ----
def calculate_base_score(worker, max_salary: float):
    normalized = normalize_features(worker, max_salary)

    score = 0
    for key, weight in WEIGHTS.items():
        score += normalized[key] * weight

    return score * 10


# ---- BAYESIAN RATING ----
def calculate_bayesian_rating(worker, global_mean: float):
    n = worker.jobs_completed
    adjusted_rating = (
        (global_mean * CONFIDENCE_M + worker.rating * n)
        / (CONFIDENCE_M + n)
    )

    return (adjusted_rating / 5) * 10


# ---- FINAL SCORE ----
def calculate_final_score(worker, global_mean: float, max_salary: float):
    base_score = calculate_base_score(worker, max_salary)
    bayesian_component = calculate_bayesian_rating(worker, global_mean)

    final_score = (0.8 * base_score) + (0.2 * bayesian_component)

    return round(final_score, 2)