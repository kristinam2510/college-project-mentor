"""
Roadmap Replanning Agent.

Deterministic, not LLM-based — this is pure scheduling logic, so it should
be predictable and explainable (important for a viva: "here is exactly why
task X moved to month Y").

How it works:
1. Figure out what month of the project we're currently in, based on
   elapsed real-world time since project.created_at.
2. Any task still "pending"/"in_progress" whose original month is already
   in the past is considered overdue.
3. Overdue tasks get pushed forward and redistributed evenly across the
   remaining months (current month onward), so no single month becomes
   overloaded. If there isn't enough room before the project's original
   end date, the roadmap "stretches" by extending duration_months — this
   keeps risk scoring honest instead of silently hiding the slip.

This does NOT call the LLM. It only rewrites `task.month` values in the DB
and lets the existing risk_agent recompute risk/success against the new
plan, so the dashboard reflects an updated, achievable schedule.
"""
import datetime
import math


def _current_project_month(created_at: datetime.datetime, duration_months: int) -> int:
    """1-indexed month number we're currently in, e.g. 1 = first month."""
    elapsed_days = max((datetime.datetime.utcnow() - created_at).days, 0)
    month = math.floor(elapsed_days / 30) + 1
    return max(1, month)


def replan_if_needed(project: dict, tasks: list[dict]) -> dict:
    """
    project: dict with at least duration_months, created_at
    tasks: list of dicts with at least id, month, status (mutated in place
           on the 'new_month' key for any task that needs to move)

    Returns:
        {
            "changed": bool,
            "current_month": int,
            "new_duration_months": int,
            "moves": [ {"task_id": ..., "old_month": ..., "new_month": ...}, ... ],
        }
    """
    created_at = project["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.datetime.fromisoformat(created_at)

    duration_months = project["duration_months"]
    current_month = _current_project_month(created_at, duration_months)

    overdue = [t for t in tasks if t["status"] != "done" and t["month"] < current_month]

    if not overdue:
        return {
            "changed": False,
            "current_month": current_month,
            "new_duration_months": duration_months,
            "moves": [],
        }

    # Not-yet-done tasks already scheduled in current month or later — these
    # keep their slot but count toward each month's load when redistributing.
    upcoming = [t for t in tasks if t["status"] != "done" and t["month"] >= current_month]

    # How many months do we have left to work with? Start with the original
    # remaining months; if overdue tasks don't fit reasonably (more than
    # ~4 tasks/month average), extend duration_months so the plan stays
    # realistic rather than just cramming everything into what's left.
    months_remaining = max(duration_months - current_month + 1, 1)
    total_to_place = len(overdue) + len(upcoming)
    max_tasks_per_month = 4  # keep months from becoming unrealistic

    needed_months = max(months_remaining, math.ceil(total_to_place / max_tasks_per_month))
    new_duration_months = max(duration_months, current_month + needed_months - 1)

    # Build month buckets from current_month..new_duration_months, seeded
    # with the upcoming (not-yet-overdue) tasks first, then fill remaining
    # capacity with overdue tasks, evenly spread.
    month_range = list(range(current_month, new_duration_months + 1))
    buckets = {m: [] for m in month_range}

    for t in upcoming:
        target = t["month"] if t["month"] in buckets else month_range[-1]
        buckets[target].append(t)

    # Distribute overdue tasks into whichever upcoming month currently has
    # the fewest tasks, round-robin style, so the load stays balanced.
    for t in overdue:
        target_month = min(month_range, key=lambda m: len(buckets[m]))
        buckets[target_month].append(t)

    moves = []
    for month, bucket_tasks in buckets.items():
        for t in bucket_tasks:
            if t["month"] != month:
                moves.append({"task_id": t["id"], "old_month": t["month"], "new_month": month})
                t["new_month"] = month

    return {
        "changed": True,
        "current_month": current_month,
        "new_duration_months": new_duration_months,
        "moves": moves,
    }