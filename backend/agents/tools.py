from __future__ import annotations

import re

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from app.schemas import DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever


def extract_ticket_priority(query: str) -> str | None:
    match = re.search(r"\bp([123])\b", query.lower())
    if not match:
        return None
    return f"P{match.group(1)}"


def is_ticket_query(query: str) -> bool:
    q = query.lower()
    return any(
        keyword in q
        for keyword in (
            "ticket",
            "tickets",
            "incident",
            "incidents",
            "p1",
            "p2",
            "p3",
        )
    )


class DocumentSearchTool:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    def run(self, query: str) -> list[DocumentChunk]:
        chunks = self.retriever.retrieve(query)
        return [
            chunk for chunk in chunks if chunk.metadata.get("doc_type") != "ticket"
        ]


class TicketLookupTool:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    def run(self, query: str) -> list[DocumentChunk]:
        priority = extract_ticket_priority(query)
        ticket_chunks = self.retriever.retrieve_tickets(query, priority=priority)
        if ticket_chunks:
            return ticket_chunks
        if priority:
            return self.retriever.retrieve_tickets(query, priority=None)
        return []


class SummarizerTool:
    def run(
        self, query: str, chunks: list[DocumentChunk], ticket_first: bool = False
    ) -> tuple[str, bool]:
        if not chunks:
            return (
                "No relevant context was found to summarize for this question.",
                True,
            )

        ordered_chunks = chunks
        if ticket_first:
            ticket_chunks = [
                chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"
            ]
            other_chunks = [
                chunk for chunk in chunks if chunk.metadata.get("doc_type") != "ticket"
            ]
            ordered_chunks = ticket_chunks + other_chunks

        context = "\n\n".join(
            f"[{index + 1}] {chunk.text[:700]}"
            for index, chunk in enumerate(ordered_chunks[:8])
        )
        system_prompt = (
            "You are an enterprise knowledge assistant. Summarize and answer using ONLY "
            "the provided context. Cite sources inline using [N]. If the question is about "
            "support tickets, prioritize ticket entries over SOP documents. If context is "
            "insufficient, say so and recommend escalation."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer (cite with [N]):"
        answer = call_llm(prompt, system_prompt=system_prompt)
        retrieval_only = answer.startswith(LLM_FAILURE_PREFIX)
        return answer, retrieval_only
