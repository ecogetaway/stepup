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


def _build_retrieval_fallback_answer(query: str, chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return (
            "I could not find relevant information in the knowledge base for this question. "
            "Please escalate to a human support agent."
        )

    lines = [
        f"Based on retrieved enterprise documents, here is what applies to: {query}",
        "",
    ]
    for index, chunk in enumerate(chunks[:3]):
        source = chunk.metadata.get("source", "unknown")
        excerpt = chunk.text.strip().replace("\n", " ")
        if len(excerpt) > 280:
            excerpt = f"{excerpt[:277]}..."
        lines.append(f"- [{index + 1}] From {source}: {excerpt}")

    lines.extend(
        [
            "",
            "Answer synthesized from retrieved sources because the hosted LLM is unavailable.",
        ]
    )
    return "\n".join(lines)


class ReActAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever
        self._trace: list[dict] = []

    def run(self, query: str) -> dict:
        self._trace = []
        self._trace.append({"step": "retrieve", "tool": "hybrid_retriever"})
        chunks = self.retriever.retrieve(query)
        self._trace.append({"step": "context_built", "chunks_used": len(chunks)})
        context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))
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
