from app.schemas import DocumentChunk, Citation
from retrieval.hybrid_retriever import HybridRetriever
from app.config import settings
import logging
import math

logger = logging.getLogger(__name__)


def _normalise_overlap_score(score: float | None) -> float:
    if score is None:
        return 0.0
    if 0.0 <= score <= 1.0:
        return float(score)
    return float(1.0 / (1.0 + math.exp(-score)))

try:
    import httpx

    HAS_HTTPX = True
except ModuleNotFoundError:
    HAS_HTTPX = False


def _call_ollama(prompt: str, system_prompt: str | None = None) -> str:
    if not HAS_HTTPX:
        return "[DEMO FALLBACK] httpx not installed. Install it to enable live LLM calls."
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    if system_prompt:
        payload["system"] = system_prompt
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip() or "[DEMO FALLBACK] Empty response from Ollama."
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
        return (
            f"[DEMO FALLBACK] Ollama unreachable at {settings.OLLAMA_BASE_URL}. "
            f"Start Ollama or check the URL. Error: {exc}"
        )


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
        return _call_ollama(prompt, system_prompt=system_prompt)
