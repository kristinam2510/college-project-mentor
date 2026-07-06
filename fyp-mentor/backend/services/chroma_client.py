"""
ChromaDB wrapper. Stores paper abstracts per-project so the Research Gap
Agent can retrieve the right context, and so papers are only fetched once
per project (cheap caching) instead of re-hitting arXiv/Semantic Scholar
every time the gap/roadmap agents need context.
"""
import chromadb

_chroma_client = None


def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="./chroma_store")
    return _chroma_client


def get_collection(project_id: str):
    client = get_chroma()
    return client.get_or_create_collection(name=f"project_{project_id}")


def store_papers(project_id: str, papers: list[dict]):
    collection = get_collection(project_id)
    if not papers:
        return
    collection.upsert(
        ids=[f"{p['source']}_{i}" for i, p in enumerate(papers)],
        documents=[f"{p['title']}\n\n{p['summary']}" for p in papers],
        metadatas=[
            {"title": p["title"], "url": p["url"], "source": p["source"]}
            for p in papers
        ],
    )


def query_papers(project_id: str, query: str, n_results: int = 6) -> list[dict]:
    collection = get_collection(project_id)
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))
    out = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        out.append({"text": doc, **meta})
    return out
