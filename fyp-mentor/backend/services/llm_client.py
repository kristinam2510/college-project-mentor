"""
Thin wrapper around an LLM API.

Every "agent" in this project is really just: a focused prompt + a JSON schema
+ this one client. There is no need for a heavyweight agent framework to run
a fixed, sequential pipeline (form -> ideas -> research -> gaps -> architecture
-> roadmap). CrewAI's value is when agents need to dynamically decide which
tool to call next; here the order is fixed, so plain function calls are
simpler to build, debug, and explain in a viva.

Uses Groq (https://console.groq.com) by default — free API key, no billing
required, OpenAI-compatible endpoint, fast open models like Llama 3.3 70B.

To switch providers, change GROQ_BASE_URL / GROQ_MODEL in .env, or swap this
file's client setup for Anthropic/OpenAI directly — the ask_json() interface
used by every agent stays the same either way.
"""
import json
import os
import re
from openai import OpenAI

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at "
                "https://console.groq.com/keys and add it to backend/.env"
            )
        _client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        timeout=30.0,  # seconds
)
    return _client


def ask_json(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict | list:
    """
    Calls the model and forces a JSON-only response.
    Retries automatically if the model returns invalid JSON.
    """

    client = get_client()
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    last_error = None

    for attempt in range(3):

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        + "\n\nIMPORTANT:\n"
                          "- Respond ONLY with valid JSON.\n"
                          "- No markdown.\n"
                          "- No explanation.\n"
                          "- Complete every object and array.\n"
                          "- Never truncate the response."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
        )

        text = response.choices[0].message.content.strip()

        # Remove markdown fences if present
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

        try:
            return json.loads(text)

        except json.JSONDecodeError as e:
            last_error = e

            print(f"\nAttempt {attempt+1}/3")
            print(text[:800])

    raise ValueError(
        f"Model did not return valid JSON after 3 attempts.\n"
        f"Last error: {last_error}"
    )