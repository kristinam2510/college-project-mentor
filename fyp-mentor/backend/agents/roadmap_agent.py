from services.llm_client import ask_json

SYSTEM = """You create realistic month-by-month project plans for student
teams, accounting for university schedules (exams, breaks) being unknown,
so keep tasks generic but well-scoped and sequenced sensibly (research
before build, build before test)."""


def _normalize_months(roadmap: dict) -> dict:
    """
    Defensively normalize month entries. Some models occasionally return
    {"1": {"theme": ..., "tasks": [...]}} instead of the requested
    {"month": 1, "theme": ..., "tasks": [...]}. This converts either shape
    into the flat {"month": int, ...} form the rest of the app expects.
    """
    fixed = []
    for block in roadmap.get("months", []):
        if "month" in block:
            fixed.append(block)
            continue
        # handle {"1": {...}} shape
        for key, value in block.items():
            try:
                month_num = int(key)
            except (ValueError, TypeError):
                continue
            normalized = {"month": month_num, **value}
            fixed.append(normalized)
    roadmap["months"] = fixed
    return roadmap


def generate_roadmap(title: str, description: str, duration_months: int, team_size: int) -> dict:
    prompt = f"""
Project: {title}
Description: {description}
Duration: {duration_months} months
Team size: {team_size}

Create a month-by-month roadmap. Return a flat JSON object in EXACTLY this
shape, with "month" as a field (NOT as a dictionary key):

{{
  "months": [
    {{
      "month": 1,
      "theme": "Research & Literature Survey",
      "tasks": ["Task one", "Task two", "Task three"],
      "milestone": "One sentence describing what should be true at month end."
    }},
    {{
      "month": 2,
      "theme": "...",
      "tasks": ["..."],
      "milestone": "..."
    }}
  ]
}}

Rules:
- "month" must be an integer field inside each object, never a dictionary key like "1": {{...}}.
- "tasks" must be an array of 3-6 short, concrete, checkable task strings.
- Return exactly {duration_months} entries, one per month, numbered 1 to {duration_months}.
- Do not nest month objects under numeric keys. Follow the example shape exactly.
"""
    result = ask_json(SYSTEM, prompt, max_tokens=2500)
    return _normalize_months(result)


REPLAN_SYSTEM = """You are a project mentor adjusting a student's plan based
on real progress. If they are behind schedule, compress, merge, or cut
lower-priority tasks in the remaining months so the project is still
finishable on time -- be concrete about what to drop or simplify, don't just
add more hours. If they are ahead of schedule, pull in stretch goals,
deepen evaluation/testing, or add polish tasks (e.g. additional
experiments, a stronger writeup) rather than leaving the timeline slack
unused. Never simply repeat the original plan unchanged."""


def regenerate_roadmap(
    title: str,
    description: str,
    duration_months: int,
    team_size: int,
    current_month: int,
    tasks: list[dict],
    risk: dict,
) -> dict:
    done = [t["title"] for t in tasks if t["status"] == "done"]
    pending = [t["title"] for t in tasks if t["status"] != "done"]

    prompt = f"""
Project: {title}
Description: {description}
Total duration: {duration_months} months
Team size: {team_size}
We are currently in month {current_month}.

Risk level: {risk['risk_level']} ({risk['risk_score']}/100)
Success probability: {risk['success_probability']}%
Blockers: {', '.join(risk['potential_blockers'])}

Tasks already completed:
{chr(10).join(f'- {t}' for t in done) or 'None yet'}

Tasks still pending from the original plan:
{chr(10).join(f'- {t}' for t in pending) or 'None'}

Re-plan the roadmap from month {current_month} through month {duration_months}
only (do not include months before {current_month}).

Return a flat JSON object in EXACTLY this shape, with "month" as a field
(NOT as a dictionary key):

{{
  "months": [
    {{
      "month": {current_month},
      "theme": "...",
      "tasks": ["Task one", "Task two", "Task three"],
      "milestone": "One sentence."
    }}
  ]
}}

Rules:
- "month" must be an integer field inside each object, never a dictionary key like "{current_month}": {{...}}.
- "tasks" must be an array of 3-6 short, concrete, checkable strings.
- Cover months {current_month} through {duration_months} only.
"""
    result = ask_json(REPLAN_SYSTEM, prompt, max_tokens=2500)
    return _normalize_months(result)