"""
Risk & Success Prediction Agent.

Deliberately rule-based rather than a trained ML model: with a single
student team and no historical FYP dataset to train on, a "trained model"
would either be trivial (overfit to nothing) or fabricated. A transparent,
weighted heuristic is more honest, easier to defend in a viva ("here is
exactly why it predicted this"), and still computes a genuine numeric
score from real signals (schedule adherence, task velocity, complexity,
team size). If you later collect real usage data across multiple cohorts,
this is the natural place to swap in a trained logistic regression model
without changing the API contract below.
"""
import datetime


def _schedule_adherence(tasks: list[dict]) -> float:
    """% of tasks that are done or on track relative to elapsed time."""
    if not tasks:
        return 1.0
    done = sum(1 for t in tasks if t["status"] == "done")
    return done / len(tasks)


def assess_risk_and_success(
    project: dict,
    tasks: list[dict],
) -> dict:
    duration_months = project["duration_months"]
    team_size = project["team_size"]
    difficulty = project["difficulty"]

    created_at = project["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.datetime.fromisoformat(created_at)
    elapsed_months = max(
        (datetime.datetime.utcnow() - created_at).days / 30.0, 0.01
    )
    expected_progress = min(elapsed_months / max(duration_months, 1), 1.0)

    adherence = _schedule_adherence(tasks)
    completion_gap = expected_progress - adherence  # positive = behind schedule

    # --- weighted heuristic scoring (0-100, higher = worse risk) ---
    difficulty_weight = {"Easy": 5, "Medium": 15, "Hard": 25}.get(difficulty, 15)
    team_penalty = 10 if team_size == 1 else 0  # solo projects have less slack
    schedule_penalty = max(completion_gap, 0) * 100  # behind-schedule penalty

    risk_score = min(100, round(difficulty_weight + team_penalty + schedule_penalty))
    risk_level = "Low" if risk_score < 30 else "Medium" if risk_score < 60 else "High"

    success_probability = max(5, min(95, round(100 - risk_score * 0.8)))

    expected_completion_offset_months = round(max(completion_gap, 0) * duration_months, 1)
    expected_completion = (
        created_at + datetime.timedelta(days=30 * (duration_months + expected_completion_offset_months))
    ).date().isoformat()

    factors = []
    if schedule_penalty > 0:
        factors.append(
            f"Project is {round(completion_gap*100)}% behind expected progress "
            f"({round(adherence*100)}% of tasks done vs {round(expected_progress*100)}% of timeline elapsed)."
        )
    else:
        factors.append("Task completion is keeping pace with the elapsed timeline.")
    factors.append(f"Difficulty level '{difficulty}' contributes a baseline risk of {difficulty_weight} points.")
    if team_penalty:
        factors.append("Solo team size reduces parallelism and slack for setbacks.")

    blockers = []
    pending_high_priority = [t for t in tasks if t["status"] == "pending"]
    if len(pending_high_priority) > len(tasks) * 0.5 and tasks:
        blockers.append("More than half of all planned tasks are still untouched.")
    if completion_gap > 0.25:
        blockers.append("Schedule slippage exceeds 25% - re-plan upcoming milestones.")
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "success_probability": success_probability,
        "expected_completion_date": expected_completion,
        "explanation_factors": factors,
        "potential_blockers": blockers or ["No major blockers detected from current data."],
    }
