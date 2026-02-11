# app/analytics.py

def calculate_employability(worker):
    """
    Rule-based employability scoring.
    Can be replaced by ML later without changing API.
    """

    score = 3
    reasons = []

    if worker.experience_years >= 2:
        score += 2
        reasons.append("Has at least 2 years experience")

    if worker.experience_years >= 5:
        score += 2
        reasons.append("Has 5+ years experience")

    if worker.skill.lower() in ["delivery", "cleaning", "driver"]:
        score += 1
        reasons.append("High-demand skill")

    if worker.salary <= 20000:
        score += 2
        reasons.append("Cost-effective salary")

    return min(score, 10), reasons