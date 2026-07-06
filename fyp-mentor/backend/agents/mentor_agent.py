"""
Dynamic Mentor Agent.

Per the brief: NOT a chatbot. This runs as a periodic check (called when the
dashboard loads, or on a schedule) that compares planned roadmap vs actual
task status + the risk assessment, and returns a short list of status
messages / next steps to show as cards on the dashboard.
"""
import datetime
from services.llm_client import ask_json

SYSTEM = """You are a sharp, experienced project supervisor for student
final-year projects. You give short, specific, brutally honest but
constructive status updates.

Your advice must:
- Name specific tasks from the task list (never speak in generalities like
  "continue working on your tasks")
- Suggest concrete parallelisation where tasks can be done simultaneously
  to save time (e.g. "Start X while Y is running")
- Flag the single biggest risk to the deadline by name
- Give at least one "speed-up" tip per update — a practical shortcut,
  tool, or technique the team can use RIGHT NOW to move faster
- Judge progress relative to elapsed timeline percentage ONLY — a team
  on day 2 of a 4-month project is NOT behind even if 0 tasks are done
- Never use vague phrases like "stay focused", "keep it up", "make sure
  to", "ensure you", or "it is important to" — be direct and specific"""


def mentor_check(
    project_title: str,
    roadmap: dict,
    tasks: list[dict],
    risk: dict,
    project: dict = None,
) -> dict:

    done_tasks = [t for t in tasks if t["status"] == "done"]
    pending_tasks = [t for t in tasks if t["status"] != "done"]

    task_lines = "\n".join(
        f"- [{t['status'].upper()}] Week {(t['month']-1)*4+1}–{t['month']*4}: {t['title']}"
        for t in tasks
    )

    # Upcoming tasks (next 3 pending) for targeted advice
    upcoming = pending_tasks[:3]
    upcoming_lines = "\n".join(
        f"- Week {(t['month']-1)*4+1}–{t['month']*4}: {t['title']}"
        for t in upcoming
    )

    # Elapsed time grounding
    elapsed_note = ""
    current_week = 1
    total_weeks = 16
    elapsed_pct = 0

    if project:
        created_at = project.get("created_at")
        duration_months = project.get("duration_months", 4)
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)
        if created_at and duration_months:
            elapsed_days = max((datetime.datetime.utcnow() - created_at).days, 0)
            total_days = duration_months * 30
            elapsed_pct = round(min(elapsed_days / total_days * 100, 100))
            current_week = max(elapsed_days // 7 + 1, 1)
            total_weeks = duration_months * 4
            tasks_due_pct = round(len(done_tasks) / max(len(tasks), 1) * 100)
            pace_note = (
                "AHEAD of schedule" if tasks_due_pct > elapsed_pct + 10
                else "BEHIND schedule" if tasks_due_pct < elapsed_pct - 10
                else "ON TRACK"
            )
            elapsed_note = (
                f"\nTimeline: Week {current_week} of {total_weeks} "
                f"({elapsed_pct}% of project elapsed). "
                f"Tasks completed: {len(done_tasks)}/{len(tasks)} "
                f"({tasks_due_pct}%). Pace assessment: {pace_note}."
            )

    # Roadmap context — what should be happening this week
    current_month = max((current_week - 1) // 4 + 1, 1)
    current_month_plan = next(
        (m for m in roadmap.get("months", []) if m.get("month") == current_month),
        None,
    )
    month_context = ""
    if current_month_plan:
        month_context = (
            f"\nCurrent month ({current_month}) theme: {current_month_plan.get('theme', '')}"
            f"\nMonth milestone: {current_month_plan.get('milestone', '')}"
            f"\nMonth tasks: {', '.join(current_month_plan.get('tasks', []))}"
        )

    prompt = f"""
Project: {project_title}
{elapsed_note}
{month_context}

All tasks:
{task_lines or 'No tasks recorded yet.'}

Next 3 upcoming tasks:
{upcoming_lines or 'None — all tasks complete!'}

Risk assessment:
- Risk level: {risk['risk_level']} ({risk['risk_score']}/100)
- Success probability: {risk['success_probability']}%
- Blockers: {', '.join(risk.get('potential_blockers', []))}
- Expected completion: {risk.get('expected_completion_date', 'unknown')}

Write a mentor status update. Return JSON with exactly these keys:

{{
  "headline": "One direct sentence on current pace — name a specific task if relevant",
  "pace_status": "one of: on_track | ahead | behind",
  "next_steps": [
    "Specific action on a named task — include a speed-up tip or tool where relevant",
    "Another specific action, suggest parallelising with another task if possible",
    "One concrete speed-up tip — a tool, technique, or shortcut for the hardest upcoming task"
  ],
  "biggest_risk": "If behind/on_track: the single most likely reason this project misses its deadline. If ahead: the upcoming task most likely to slow momentum — frame it as a heads-up, not a warning",
  "encouragement": "One honest sentence — only positive if the data supports it, otherwise a direct motivational push"
}}

Rules:
- next_steps must be 2–4 items, each referencing a real task name from the list
- biggest_risk must name a specific task or pattern, not a generic phrase
- Never say "ensure", "make sure", "it is important", "stay focused"
- Speed-up tips should name real tools (e.g. HuggingFace, Kaggle, sklearn, pandas, FAISS)
"""
    return ask_json(SYSTEM, prompt, max_tokens=1000)