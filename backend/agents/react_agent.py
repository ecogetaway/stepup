import logging
import re

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from app.schemas import DocumentChunk, Citation
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.scoring import chunk_overlap_score

logger = logging.getLogger(__name__)

MAX_CONTEXT_CHUNKS = 3
MAX_CHUNK_CHARS = 700


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
        answer, retrieval_only = self._generate_answer(query, context, chunks)
        citations = [
            Citation(
                source_title=c.metadata.get("source", "unknown"),
                source_url=c.metadata.get("source_url", ""),
                chunk_text=c.text[:200],
                overlap_score=chunk_overlap_score(c, rank),
                doc_type=c.metadata.get("doc_type", "unknown"),
            )
            for rank, c in enumerate(chunks)
        ]
        self._trace.append({"step": "citations_attached", "count": len(citations)})
        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "react",
            "retrieval_only": retrieval_only,
            "trace": {"steps": self._trace},
        }

    def _generate_answer(
        self, query: str, context: str, chunks: list[DocumentChunk]
    ) -> tuple[str, bool]:
        system_prompt = (
            "You are an enterprise knowledge assistant. Answer ONLY using the provided context. "
            "Cite sources inline using [N] where N is the 1-based index of the context passage. "
            "If the context does not contain enough information, say so explicitly and suggest escalating to a human agent. "
            "Do not invent facts, URLs, or ticket IDs."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer (cite with [N]):"
        answer = call_llm(prompt, system_prompt=system_prompt)
        if answer.startswith(LLM_FAILURE_PREFIX):
            return _build_retrieval_fallback_answer(query, chunks), True
        return answer, False
