from services.llm_client import ask_json

SYSTEM = """You are a final-year-project advisor for computer science / engineering
students. You generate realistic, scoped project ideas — not vague buzzword titles.
Each idea must be achievable by a student team within the given duration."""


def generate_ideas(domain: str, difficulty: str, duration_months: int, team_size: int, sector: str | None = None) -> list[dict]:
    sector_line = f"- Sector / industry focus: {sector}" if sector else ""

    user_prompt = f"""
Generate 5 final-year project ideas for these constraints:
- Domain: {domain}
{sector_line}
- Difficulty: {difficulty}
- Duration: {duration_months} months
- Team size: {team_size}

For each idea return:
- title (string)
- description (2-3 sentences, specific, not generic)
- innovation_score (1-10)
- difficulty_score (1-10)
- industry_relevance_score (1-10)
- key_technologies (list of 3-5 strings)

Return a JSON array of 5 objects with exactly these keys:
title, description, innovation_score, difficulty_score, industry_relevance_score, key_technologies
"""
    return ask_json(SYSTEM, user_prompt, max_tokens=2500)