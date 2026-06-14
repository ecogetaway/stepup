from __future__ import annotations

from app.schemas import Citation
from retrieval.embeddings import cosine_sim, embed_query


def find_duplicate_incidents(
    citations: list[Citation], threshold: float
) -> list[list[str]]:
    """Group ticket citations whose chunk text is near-identical.

    Uses the same local embedding model as the relevance gate (no LLM call).
    Returns a list of groups; each group is a list of source titles (ticket
    IDs) that appear to describe the same underlying incident.
    """
    ticket_citations = [c for c in citations if c.doc_type == "ticket"]
    if len(ticket_citations) < 2:
        return []

    vectors: list[tuple[str, list[float]]] = []
    seen_titles: set[str] = set()
    for citation in ticket_citations:
        if citation.source_title in seen_titles:
            continue
        seen_titles.add(citation.source_title)
        text = (citation.chunk_text or "")[:400].strip()
        if not text:
            continue
        try:
            vectors.append((citation.source_title, embed_query(text)))
        except Exception:
            # Fail quiet: duplicate detection is additive, never blocks the answer.
            continue

    groups: list[list[str]] = []
    used: set[str] = set()
    for i in range(len(vectors)):
        title_i, vec_i = vectors[i]
        if title_i in used or not vec_i:
            continue
        group = [title_i]
        for j in range(i + 1, len(vectors)):
            title_j, vec_j = vectors[j]
            if title_j in used or not vec_j:
                continue
            try:
                similarity = cosine_sim(vec_i, vec_j)
            except Exception:
                continue
            if similarity >= threshold:
                group.append(title_j)
                used.add(title_j)
        if len(group) > 1:
            used.add(title_i)
            groups.append(group)

    return groups
