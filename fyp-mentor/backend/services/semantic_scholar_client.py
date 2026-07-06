"""Minimal Semantic Scholar API client."""
import os
import time
import httpx

S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,url,year,authors,citationCount,venue"


def search_semantic_scholar(query: str, max_results: int = 8, max_retries: int = 3) -> list[dict]:
    headers = {}
    api_key = os.environ.get("S2_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    params = {"query": query, "limit": max_results, "fields": FIELDS}
    last_error = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(S2_API, params=params, headers=headers)
                if resp.status_code == 429:
                    time.sleep(3 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return _parse(resp.json())
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    print(f"WARNING: Semantic Scholar search failed after {max_retries} attempts: {last_error}")
    return []


def _parse(data: dict) -> list[dict]:
    papers = []
    for item in data.get("data", []):
        papers.append({
            "title": item.get("title", ""), "summary": item.get("abstract") or "",
            "url": item.get("url", ""), "published": str(item.get("year", "")),
            "authors": [a.get("name", "") for a in item.get("authors", [])],
            "citation_count": item.get("citationCount", 0), "venue": item.get("venue", ""),
            "source": "Semantic Scholar",
        })
    return papers