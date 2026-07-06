"""Minimal arXiv API client. No API key required."""
import time
import httpx
import xml.etree.ElementTree as ET

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def search_arxiv(query: str, max_results: int = 8, max_retries: int = 3) -> list[dict]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    last_error = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(ARXIV_API, params=params)
                if resp.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"WARNING: arXiv rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return _parse(resp.text)
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
    print(f"WARNING: arXiv search failed after {max_retries} attempts: {last_error}")
    return []


def _parse(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("atom:entry", NS):
        title = entry.findtext("atom:title", default="", namespaces=NS).strip()
        summary = entry.findtext("atom:summary", default="", namespaces=NS).strip()
        link = entry.findtext("atom:id", default="", namespaces=NS).strip()
        published = entry.findtext("atom:published", default="", namespaces=NS)[:10]
        authors = [a.findtext("atom:name", default="", namespaces=NS) for a in entry.findall("atom:author", NS)]
        papers.append({"title": title, "summary": summary, "url": link, "published": published, "authors": authors, "source": "arXiv"})
    return papers