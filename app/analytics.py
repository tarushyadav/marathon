# app/analytics.py

def calculate_employability(worker):
    """
    Improved rule-based employability scoring.
    Used as pseudo-label for ML training.
    """

    score = 0
    reasons = []

    # ---- EXPERIENCE ----
    if worker.experience_years >= 5:
        score += 3
        reasons.append("Strong experience (5+ years)")
    elif worker.experience_years >= 2:
        score += 2
        reasons.append("Moderate experience (2+ years)")
    else:
        score += 1
        reasons.append("Limited experience")

    # ---- SKILL DEMAND ----
    if worker.skill.lower() in ["delivery", "cleaning", "driver"]:
        score += 1
        reasons.append("High-demand skill")

    # ---- PERFORMANCE METRICS ----
    if worker.rating >= 4.5:
        score += 2
        reasons.append("Excellent rating")
    elif worker.rating >= 3.5:
        score += 1
        reasons.append("Good rating")

    if worker.on_time >= 90:
        score += 1
        reasons.append("High punctuality")

    if worker.completion >= 90:
        score += 1
        reasons.append("High completion rate")

    # ---- COMPLAINT PENALTY ----
    if worker.complaints >= 20:
        score -= 2
        reasons.append("High complaint history")
    elif worker.complaints >= 5:
        score -= 1
        reasons.append("Some complaints reported")

    # ---- JOB VOLUME ----
    if worker.jobs_completed >= 100:
        score += 1
        reasons.append("Strong work history")

    # ---- SALARY FACTOR ----
    if worker.salary <= 20000:
        score += 1
        reasons.append("Cost-effective salary")

    # Clamp final score
    score = max(1, min(score, 10))

    return score, reasons