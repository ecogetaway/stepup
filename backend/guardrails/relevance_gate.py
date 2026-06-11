from __future__ import annotations

from app.schemas import DocumentChunk
from retrieval.embeddings import cosine_sim, embed_query

BLOCKED_PATTERNS: tuple[str, ...] = (
    "hack",
    "exploit",
    "bypass security",
    "steal",
    "crack the",
    "personal phone",
    "personal address",
    "private number",
    "home address",
    "disable logging",
    "delete the audit",
)


def is_blocked_query(query: str) -> bool:
    q = query.lower()
    return any(pattern in q for pattern in BLOCKED_PATTERNS)


def query_relevance(query: str, chunks: list[DocumentChunk]) -> float:
    """Max cosine similarity between the query and the top retrieved chunks."""
    if not chunks:
        return 0.0
    try:
        query_vec = embed_query(query)
        if not query_vec:
            return 0.0
        best = 0.0
        for chunk in chunks[:5]:
            text = (chunk.text or "")[:512].strip()
            if not text:
                continue
            best = max(best, cosine_sim(query_vec, embed_query(text)))
        return best
    except Exception:
        # Fail open: never break answering because the gate errored.
        return 1.0
