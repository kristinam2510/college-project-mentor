from services.arxiv_client import search_arxiv
from services.semantic_scholar_client import search_semantic_scholar
from services.chroma_client import store_papers
from services.llm_client import ask_json

SYSTEM = """You are a research assistant writing a literature survey for a
final-year project. You summarize accurately and never invent paper details
that were not provided to you."""


def run_research(project_id: str, title: str, description: str) -> dict:
    query = title[:150]

    arxiv_papers = search_arxiv(query, max_results=6)
    s2_papers = search_semantic_scholar(query, max_results=6)
    all_papers = arxiv_papers + s2_papers

    # cache in Chroma so the gap-detection agent can retrieve without re-fetching
    store_papers(project_id, all_papers)

    papers_text = "\n\n".join(
        f"[{i}] {p['title']} ({p.get('published','')}) - {p['source']}\n{p['summary'][:600]}"
        for i, p in enumerate(all_papers)
        if p["summary"]
    )

    user_prompt = f"""
Project: {title}
Description: {description}

Below are abstracts retrieved from arXiv and Semantic Scholar:
{papers_text}

Based ONLY on the papers above, return JSON with these keys:
- top_papers: array of up to 6 objects {{title, why_relevant (1 sentence), url}}
- research_trends: array of 3-5 strings describing current trends you observe
- state_of_the_art_techniques: array of 3-6 strings naming specific techniques/methods seen across the papers
"""
    survey = ask_json(SYSTEM, user_prompt, max_tokens=2500)
    return {"papers": all_papers, "survey": survey}
