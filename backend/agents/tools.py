from __future__ import annotations

from agents.llm import LLM_FAILURE_PREFIX, call_llm
from app.schemas import DocumentChunk
from retrieval.hybrid_retriever import HybridRetriever


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
        chunks = self.retriever.retrieve(query)
        ticket_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("doc_type") == "ticket"
        ]
        if ticket_chunks:
            return ticket_chunks
        return chunks


class SummarizerTool:
    def run(self, query: str, chunks: list[DocumentChunk]) -> tuple[str, bool]:
        if not chunks:
            return (
                "No relevant context was found to summarize for this question.",
                True,
            )

        context = "\n\n".join(
            f"[{index + 1}] {chunk.text[:700]}"
            for index, chunk in enumerate(chunks[:8])
        )
        system_prompt = (
            "You are an enterprise knowledge assistant. Summarize and answer using ONLY "
            "the provided context. Cite sources inline using [N]. If context is insufficient, "
            "say so and recommend escalation."
        )
        prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer (cite with [N]):"
        answer = call_llm(prompt, system_prompt=system_prompt)
        retrieval_only = answer.startswith(LLM_FAILURE_PREFIX)
        return answer, retrieval_only
