import logging

from agents.react_agent import _build_retrieval_fallback_answer
from agents.tools import DocumentSearchTool, SummarizerTool, TicketLookupTool
from app.schemas import Citation, DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.scoring import chunk_overlap_score

logger = logging.getLogger(__name__)


class PlanExecuteAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.document_search = DocumentSearchTool(retriever)
        self.ticket_lookup = TicketLookupTool(retriever)
        self.summarizer = SummarizerTool()
        self._trace: list[dict] = []

    def run(self, query: str) -> dict:
        self._trace = []
        sub_queries = self._decompose(query)
        self._trace.append({"step": "plan", "sub_queries": sub_queries})

        chunk_lookup: dict[str, DocumentChunk] = {}

        def merge_chunks(new_chunks: list[DocumentChunk]) -> None:
            for chunk in new_chunks:
                chunk_lookup[chunk.chunk_id] = chunk

        self._trace.append(
            {"step": "tool_call", "tool": "document_search", "query": query}
        )
        merge_chunks(self.document_search.run(query))

        self._trace.append({"step": "tool_call", "tool": "ticket_lookup", "query": query})
        merge_chunks(self.ticket_lookup.run(query))

        for sub_query in sub_queries:
            self._trace.append(
                {"step": "tool_call", "tool": "document_search", "query": sub_query}
            )
            merge_chunks(self.document_search.run(sub_query))
            self._trace.append(
                {"step": "tool_call", "tool": "ticket_lookup", "query": sub_query}
            )
            merge_chunks(self.ticket_lookup.run(sub_query))

        all_chunks = list(chunk_lookup.values())
        self._trace.append({"step": "aggregated", "total_chunks": len(all_chunks)})
        self._trace.append({"step": "tool_call", "tool": "summarizer", "query": query})

        answer, retrieval_only = self.summarizer.run(query, all_chunks)
        if retrieval_only:
            answer = _build_retrieval_fallback_answer(query, all_chunks)

        citations = [
            Citation(
                source_title=c.metadata.get("source", "unknown"),
                source_url=c.metadata.get("source_url", ""),
                chunk_text=c.text[:200],
                overlap_score=chunk_overlap_score(c, rank),
                doc_type=c.metadata.get("doc_type", "unknown"),
            )
            for rank, c in enumerate(all_chunks)
        ]

        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "plan_execute",
            "retrieval_only": retrieval_only,
            "trace": {"plan": sub_queries, "steps": self._trace},
        }

    def _decompose(self, query: str) -> list[str]:
        q = query.lower()
        if any(k in q for k in [" and ", " vs ", ", "]):
            return [
                part.strip()
                for part in query.replace(" vs ", ",").split(",")
                if part.strip()
            ]
        if any(
            k in q
            for k in [
                "last week",
                "this month",
                "p1",
                "p2",
                "p3",
                "summary",
                "summarise",
                "summarize",
                "compare",
                "breakdown",
            ]
        ):
            return [
                f"P1 incidents {query}",
                f"P2 incidents {query}",
                f"P3 incidents {query}",
                f"overall summary of {query}",
            ]
        return [query]
