from services.llm_client import ask_json

SYSTEM = """You design pragmatic, implementable system architectures for
student final-year projects. Favor well-known, well-documented technologies
a student can realistically learn within their timeline."""


def generate_architecture(title: str, description: str, key_technologies: list[str]) -> dict:
    prompt = f"""
Project: {title}
Description: {description}
Key technologies: {', '.join(key_technologies)}

Return JSON with:
- components: array of {{name, role, technology_choice, justification (1 sentence)}}
  covering at minimum: frontend, backend/API, model/ML component (if applicable),
  database, and any other necessary layer (e.g. vector store, message queue)
- data_flow: array of strings describing the flow step by step, e.g.
  "User uploads image via frontend" -> "..." (ordered list)
- tech_stack_summary: short paragraph (3-4 sentences)
"""
    return ask_json(SYSTEM, prompt, max_tokens=1500)
