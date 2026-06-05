from app.schemas import DocumentChunk, Citation
from retrieval.hybrid_retriever import HybridRetriever
import logging
import math

logger = logging.getLogger(__name__)


def _normalise_overlap_score(score: float | None) -> float:
    if score is None:
        return 0.0
    if 0.0 <= score <= 1.0:
        return float(score)
    return float(1.0 / (1.0 + math.exp(-score)))

from agents.llm import LLM_FAILURE_PREFIX, call_llm

MAX_CONTEXT_CHUNKS = 3
MAX_CHUNK_CHARS = 700


def _summarize_chunk_excerpt(text: str, max_length: int = 220) -> str:
    cleaned = " ".join(text.strip().split())
    if not cleaned:
        return ""

    for separator in (". ", "; ", " - "):
        if separator in cleaned:
            first_part = cleaned.split(separator, 1)[0].strip()
            if len(first_part) >= 40:
                cleaned = first_part
                break

    if len(cleaned) > max_length:
        cleaned = f"{cleaned[: max_length - 3].rstrip()}..."
    return cleaned


def _build_retrieval_fallback_answer(query: str, chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return (
            "I could not find relevant information in the knowledge base for this question. "
            "Please escalate to a human support agent."
        )

    primary_source = chunks[0].metadata.get("source", "enterprise documentation")
    lines = [
        f"Here is the cited guidance for **{query}** based on indexed enterprise sources:",
        "",
    ]

    for index, chunk in enumerate(chunks[:3]):
        excerpt = _summarize_chunk_excerpt(chunk.text)
        if not excerpt:
            continue
        lines.append(f"{index + 1}. {excerpt} [{index + 1}]")

    sources = sorted({chunk.metadata.get("source", "unknown") for chunk in chunks[:3]})
    lines.extend(["", f"**Sources:** {', '.join(sources)}"])
    return "\n".join(lines)


class ReActAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever
        self._trace: list[dict] = []

    def run(self, query: str, chunks: list[DocumentChunk] | None = None) -> dict:
        self._trace = []
        if chunks is None:
            self._trace.append({"step": "retrieve", "tool": "hybrid_retriever"})
            chunks = self.retriever.retrieve(query)
        else:
            self._trace.append({"step": "retrieve", "tool": "hybrid_retriever", "reused": True})
        self._trace.append({"step": "context_built", "chunks_used": len(chunks)})
        context_chunks = chunks[:MAX_CONTEXT_CHUNKS]
        context = "\n\n".join(
            f"[{i + 1}] {c.text[:MAX_CHUNK_CHARS]}"
            for i, c in enumerate(context_chunks)
        )
        answer = self._generate_answer(query, context, chunks)
        citations = [
            Citation(
                source_title=c.metadata.get("source", "unknown"),
                source_url=c.metadata.get("source_url", ""),
                chunk_text=c.text[:200],
                overlap_score=_normalise_overlap_score(c.rerank_score),
                doc_type=c.metadata.get("doc_type", "unknown"),
            )
            for c in chunks
        ]
        self._trace.append({"step": "citations_attached", "count": len(citations)})
        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "react",
            "trace": {"steps": self._trace},
        }

    def _generate_answer(self, query: str, context: str, chunks: list[DocumentChunk]) -> str:
        system_prompt = (
            "You are an enterprise knowledge assistant. Answer ONLY using the provided context. "
            "Cite sources inline using [N] where N is the 1-based index of the context passage. "
            "If the context does not contain enough information, say so explicitly and suggest escalating to a human agent. "
            "Do not invent facts, URLs, or ticket IDs."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer (cite with [N]):"
        answer = call_llm(prompt, system_prompt=system_prompt)
        if answer.startswith(LLM_FAILURE_PREFIX):
            return _build_retrieval_fallback_answer(query, chunks)
        return answer
