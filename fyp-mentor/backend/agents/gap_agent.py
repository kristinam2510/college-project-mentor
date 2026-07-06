"""
Research Gap Detection Agent.

Method (explainable, not a black box — good for the report's "novelty"
section):
1. Take the abstracts already retrieved by the Research Agent (cached in
   Chroma).
2. Ask the LLM to extract, per paper, the core method/architecture used
   (a structured tag, e.g. "CNN", "Transformer", "GAN", "rule-based").
3. Compute a simple frequency count of methods across papers in code
   (not the LLM) -- this is the "common approaches" signal.
4. Feed the frequency table + abstracts back to the LLM and ask it to
   reason about combinations / directions that are rare or absent,
   and justify each suggested gap with which papers support the claim.

Step 3 being done in plain Python (not by the LLM) is the part worth
highlighting in your report: it makes the "most papers use X" claims
auditable and reproducible rather than an LLM guess.
"""
from collections import Counter
from services.chroma_client import query_papers
from services.llm_client import ask_json

SYSTEM_TAG = """You are tagging research papers by core method. Be terse and
use a small controlled vocabulary where possible (e.g. CNN, Transformer,
RNN/LSTM, GAN, Vision Transformer, Reinforcement Learning, Classical ML,
Rule-based, Hybrid, Other)."""

SYSTEM_GAP = """You are a research advisor identifying underexplored research
directions. Ground every claim in the evidence given. Do not invent papers
or statistics that are not implied by the data provided."""


def _tag_methods(papers: list[dict]) -> list[dict]:
    if not papers:
        return []
    listing = "\n".join(f"[{i}] {p['title']}: {p['summary'][:400]}" for i, p in enumerate(papers))
    prompt = f"""
Here are paper titles and abstracts:
{listing}

For each paper (by index), return its core method tag.
Return a JSON array of objects: {{"index": int, "method": string}}
"""
    tags = ask_json(SYSTEM_TAG, prompt, max_tokens=1500)
    return tags


def detect_gaps(project_id: str, title: str, description: str, papers: list[dict]) -> dict:
    tagged = _tag_methods(papers)

    # auditable frequency count, computed in plain Python
    method_counts = Counter(t["method"] for t in tagged if "method" in t)
    total = sum(method_counts.values()) or 1
    method_distribution = [
        {"method": m, "count": c, "percentage": round(100 * c / total, 1)}
        for m, c in method_counts.most_common()
    ]

    distribution_text = "\n".join(
        f"- {m['method']}: {m['count']} papers ({m['percentage']}%)" for m in method_distribution
    )

    prompt = f"""
Project: {title}
Description: {description}

Method distribution observed across {len(papers)} retrieved papers:
{distribution_text}

Based on this distribution and your knowledge of the field, identify 3-5
potential research gaps / novel directions for this student project. For
each gap return:
- gap_statement (1-2 sentences, specific)
- evidence (why the distribution above suggests this is underexplored)
- feasibility_for_student (Low/Medium/High, given this is a student FYP not a PhD)
- suggested_approach (2-3 sentences on how to implement/validate it)

Return JSON: {{"gaps": [...]}}
"""
    gap_result = ask_json(SYSTEM_GAP, prompt, max_tokens=2000)

    return {
        "method_distribution": method_distribution,
        "gaps": gap_result.get("gaps", gap_result if isinstance(gap_result, list) else []),
    }
