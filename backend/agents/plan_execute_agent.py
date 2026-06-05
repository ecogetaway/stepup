from app.schemas import DocumentChunk, Citation
from retrieval.hybrid_retriever import HybridRetriever
import logging
from agents.react_agent import _normalise_overlap_score

logger = logging.getLogger(__name__)

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from agents.react_agent import _build_retrieval_fallback_answer


class PlanExecuteAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever
        self._trace: list[dict] = []

    def run(self, query: str) -> dict:
        self._trace = []
        sub_queries = self._decompose(query)
        self._trace.append({"step": "plan", "sub_queries": sub_queries})
        tool_results: dict[str, list[DocumentChunk]] = {}
        for sq in sub_queries:
            self._trace.append({"step": "tool_call", "query": sq, "tool": "hybrid_retriever"})
            tool_results[sq] = self.retriever.retrieve(sq)
        all_chunks = [c for chunks in tool_results.values() for c in chunks]
        context = "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(all_chunks))
        answer = self._generate_answer(query, context, all_chunks)
        citations = [
            Citation(
                source_title=c.metadata.get("source", "unknown"),
                source_url=c.metadata.get("source_url", ""),
                chunk_text=c.text[:200],
                overlap_score=_normalise_overlap_score(c.rerank_score),
                doc_type=c.metadata.get("doc_type", "unknown"),
            )
            for c in all_chunks
        ]
        self._trace.append({"step": "aggregated", "total_chunks": len(all_chunks)})
        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "plan_execute",
            "trace": {"plan": sub_queries, "steps": self._trace},
        }

    def _decompose(self, query: str) -> list[str]:
        q = query.lower()
        if any(k in q for k in [" and ", " vs ", ", "]):
            return [part.strip() for part in query.replace(" vs ", ",").split(",") if part.strip()]
        if any(k in q for k in ["last week", "this month", "p1", "p2", "p3", "summary", "summarise", "summarize", "compare", "breakdown"]):
            return [
                f"P1 incidents {query}",
                f"P2 incidents {query}",
                f"P3 incidents {query}",
                f"overall summary of {query}",
            ]
        return [query]

    def _generate_answer(self, query: str, context: str, chunks: list[DocumentChunk]) -> str:
        system_prompt = (
            "You are an enterprise knowledge assistant performing analytical reasoning. "
            "Use ONLY the provided context. Cite sources inline using [N]. "
            "If the context is insufficient, say so and recommend escalation."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer (cite with [N]):"
        answer = call_llm(prompt, system_prompt=system_prompt)
        if answer.startswith(LLM_FAILURE_PREFIX):
            return _build_retrieval_fallback_answer(query, chunks)
        return answer
