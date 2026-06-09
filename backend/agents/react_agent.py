import logging
import re

from agents.tools import DocumentSearchTool, SummarizerTool
from app.schemas import DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever
from services.citations import build_citation_from_chunk

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHUNKS = 3


def _strip_demo_boilerplate(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    for prefix in (
        "Enterprise Knowledge Copilot Sample SOP ",
        "Enterprise Knowledge Copilot ",
    ):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
    return cleaned


def _summarize_chunk_excerpt(text: str, max_length: int = 240) -> str:
    cleaned = _strip_demo_boilerplate(text)
    if not cleaned:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]
    candidates = [sentence for sentence in sentences if len(sentence) >= 35]
    if not candidates:
        candidates = [cleaned]

    best = max(candidates[:6], key=len)
    if len(best) > max_length:
        trimmed = best[: max_length - 3].rsplit(" ", 1)[0].strip()
        best = f"{trimmed}..." if trimmed else f"{best[: max_length - 3]}..."
    return best


def _build_retrieval_fallback_answer(query: str, chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return (
            "I could not find relevant information in the knowledge base for this question. "
            "Please escalate to a human support agent."
        )

    from agents.tools import is_ticket_query

    scoped_chunks = chunks
    if is_ticket_query(query):
        ticket_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"
        ]
        if ticket_chunks:
            scoped_chunks = ticket_chunks

    lines = [
        f"Here is the cited guidance for **{query}** based on indexed enterprise sources:",
        "",
    ]

    for index, chunk in enumerate(scoped_chunks[:MAX_CONTEXT_CHUNKS]):
        excerpt = _summarize_chunk_excerpt(chunk.text)
        if not excerpt:
            continue
        lines.append(f"{index + 1}. {excerpt} [{index + 1}]")

    sources = sorted(
        {chunk.metadata.get("source", "unknown") for chunk in scoped_chunks[:MAX_CONTEXT_CHUNKS]}
    )
    lines.extend(["", f"**Sources:** {', '.join(sources)}"])
    return "\n".join(lines)


class ReActAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.document_search = DocumentSearchTool(retriever)
        self.summarizer = SummarizerTool()
        self._trace: list[dict] = []

    def run(self, query: str, chunks: list[DocumentChunk] | None = None) -> dict:
        self._trace = []
        if chunks is None:
            self._trace.append(
                {"step": "tool_call", "tool": "document_search", "query": query}
            )
            chunks = self.document_search.run(query)
        else:
            self._trace.append(
                {"step": "tool_call", "tool": "document_search", "query": query, "reused": True}
            )

        self._trace.append({"step": "context_built", "chunks_used": len(chunks)})
        self._trace.append({"step": "tool_call", "tool": "summarizer", "query": query})
        answer, retrieval_only = self.summarizer.run(query, chunks)
        if retrieval_only:
            answer = _build_retrieval_fallback_answer(query, chunks)

        citations = [build_citation_from_chunk(chunk, rank) for rank, chunk in enumerate(chunks)]
        self._trace.append({"step": "citations_attached", "count": len(citations)})
        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "react",
            "retrieval_only": retrieval_only,
            "trace": {"steps": self._trace},
        }
