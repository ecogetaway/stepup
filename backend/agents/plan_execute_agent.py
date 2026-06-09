import logging

from agents.react_agent import _build_retrieval_fallback_answer
from agents.sla_analytics import aggregate, format_sla_context, is_sla_query
from agents.tools import (
    DocumentSearchTool,
    SummarizerTool,
    TicketLookupTool,
    is_ticket_query,
)
from app.schemas import DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever
from services.citations import build_citation_from_chunk

logger = logging.getLogger(__name__)

MAX_CITATIONS = 8


def _order_chunks_for_query(query: str, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    if not is_ticket_query(query):
        return chunks

    ticket_chunks = [
        chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"
    ]
    other_chunks = [
        chunk for chunk in chunks if chunk.metadata.get("doc_type") != "ticket"
    ]
    return ticket_chunks + other_chunks


class PlanExecuteAgent:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.document_search = DocumentSearchTool(retriever)
        self.ticket_lookup = TicketLookupTool(retriever)
        self.summarizer = SummarizerTool()
        self._trace: list[dict] = []

    def run(self, query: str) -> dict:
        self._trace = []
        sla_summary = None
        ticket_focused = is_ticket_query(query)
        sub_queries = self._decompose(query)
        self._trace.append({"step": "plan", "sub_queries": sub_queries})

        chunk_lookup: dict[str, DocumentChunk] = {}

        def merge_chunks(new_chunks: list[DocumentChunk]) -> None:
            for chunk in new_chunks:
                chunk_lookup[chunk.chunk_id] = chunk

        self._trace.append(
            {"step": "tool_call", "tool": "ticket_lookup", "query": query}
        )
        merge_chunks(self.ticket_lookup.run(query))

        if not ticket_focused:
            self._trace.append(
                {"step": "tool_call", "tool": "document_search", "query": query}
            )
            merge_chunks(self.document_search.run(query))

        for sub_query in sub_queries:
            self._trace.append(
                {"step": "tool_call", "tool": "ticket_lookup", "query": sub_query}
            )
            merge_chunks(self.ticket_lookup.run(sub_query))
            if not ticket_focused:
                self._trace.append(
                    {"step": "tool_call", "tool": "document_search", "query": sub_query}
                )
                merge_chunks(self.document_search.run(sub_query))

        all_chunks = _order_chunks_for_query(query, list(chunk_lookup.values()))
        self._trace.append({"step": "aggregated", "total_chunks": len(all_chunks)})

        if is_sla_query(query):
            sla_summary = aggregate(query)
            self._trace.append(
                {"step": "tool_call", "tool": "sla_analytics", "summary": sla_summary}
            )

        self._trace.append({"step": "tool_call", "tool": "summarizer", "query": query})

        summarizer_query = query
        if sla_summary is not None:
            summarizer_query = (
                f"{query}\n\n{format_sla_context(sla_summary)}\n"
                "Use the deterministic SLA counts above in your answer."
            )

        answer, retrieval_only = self.summarizer.run(
            summarizer_query, all_chunks, ticket_first=ticket_focused
        )
        if retrieval_only:
            answer = _build_retrieval_fallback_answer(query, all_chunks)

        citation_chunks = all_chunks[:MAX_CITATIONS]
        citations = [
            build_citation_from_chunk(chunk, rank)
            for rank, chunk in enumerate(citation_chunks)
        ]

        return {
            "answer": answer,
            "citations": citations,
            "agent_used": "plan_execute",
            "retrieval_only": retrieval_only,
            "sla_summary": sla_summary,
            "trace": {"plan": sub_queries, "steps": self._trace},
        }

    def _decompose(self, query: str) -> list[str]:
        q = query.lower()
        if is_ticket_query(query) and any(
            keyword in q for keyword in ("summarize", "summarise", "summary", "this month")
        ):
            if "p1" in q:
                return ["P1 deployment support tickets", query]
            if "p2" in q:
                return ["P2 support tickets", query]
            if "p3" in q:
                return ["P3 support tickets", query]
            return ["open support tickets", query]

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
