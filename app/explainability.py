def derive_adjustment_reasons(worker):
    reasons = []

    if worker.jobs_completed < 10:
        reasons.append("low job history")

    if worker.complaints > 3:
        reasons.append("high complaint frequency")

    if worker.rating < 3.5:
        reasons.append("below average rating")

    return reasons

