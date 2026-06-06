from __future__ import annotations
from typing import Protocol
from app.schemas import DocumentChunk
from app.config import settings
from retrieval.embeddings import embed_query

try:
    import chromadb

    HAS_CHROMADB = True
except ModuleNotFoundError:
    HAS_CHROMADB = False

try:
    from rank_bm25 import BM25Okapi

    HAS_BM25 = True
except ModuleNotFoundError:
    HAS_BM25 = False


class RetrievalPort(Protocol):
    def search(self, query: str, top_k: int) -> list[DocumentChunk]: ...


class VectorRetriever:
    def __init__(self) -> None:
        if not HAS_CHROMADB:
            raise ModuleNotFoundError("chromadb is required.")
        self.client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR)
        )
        self.collection = self.client.get_collection(settings.CHROMA_COLLECTION)

    def search(
        self, query: str, top_k: int, where: dict | None = None
    ) -> list[DocumentChunk]:
        q_vec = embed_query(query)
        query_kwargs: dict = {
            "query_embeddings": [q_vec],
            "n_results": top_k,
        }
        if where:
            query_kwargs["where"] = where
        results = self.collection.query(**query_kwargs)
        chunks: list[DocumentChunk] = []
        for i in range(len(results["ids"][0])):
            chunks.append(
                DocumentChunk(
                    chunk_id=results["ids"][0][i],
                    doc_id=results["metadatas"][0][i].get("source", ""),
                    text=results["documents"][0][i],
                    embedding=q_vec,
                    metadata=results["metadatas"][0][i],
                )
            )
            chunks[-1].bm25_score = None
            chunks[-1].rerank_score = None
        return chunks


class BM25Retriever:
    def __init__(self) -> None:
        self._corpus_tokens: list[list[str]] = []
        self._chunk_lookup: dict[int, DocumentChunk] = {}
        self._model = None
        self._ready = False

    def index(self, chunks: list[DocumentChunk]) -> None:
        if not HAS_BM25:
            return

        self._chunk_lookup = {}
        self._corpus_tokens = []
        self._model = None
        self._ready = False

        if not chunks:
            return

        indexed_chunks: list[DocumentChunk] = []
        for chunk in chunks:
            tokens = chunk.text.lower().split()
            if not tokens:
                continue
            self._chunk_lookup[len(indexed_chunks)] = chunk
            self._corpus_tokens.append(tokens)
            indexed_chunks.append(chunk)

        if not self._corpus_tokens:
            return

        try:
            self._model = BM25Okapi(self._corpus_tokens)
            self._ready = True
        except Exception:
            self._model = None
            self._ready = False

    def search(self, query: str, top_k: int) -> list[DocumentChunk]:
        if not self._ready or self._model is None:
            return []
        tokenized = query.lower().split()
        if not tokenized:
            return []
        try:
            scores = self._model.get_scores(tokenized)
            top_indices = scores.argsort()[-top_k:][::-1]
            out: list[DocumentChunk] = []
            for idx in top_indices:
                chunk = self._chunk_lookup[int(idx)]
                chunk.bm25_score = float(scores[idx])
                out.append(chunk)
            return out
        except Exception:
            return []


def _reciprocal_rank_fusion(
    ranked_lists: list[list[DocumentChunk]],
    k: int = 60,
) -> list[tuple[DocumentChunk, float]]:
    scores: dict[str, tuple[DocumentChunk, float]] = {}
    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked):
            key = chunk.chunk_id
            rrf = 1.0 / max(k + rank + 1, 1)
            if key in scores:
                scores[key] = (chunk, scores[key][1] + rrf)
            else:
                scores[key] = (chunk, rrf)
    return sorted(scores.values(), key=lambda x: x[1], reverse=True)


class HybridRetriever:
    def __init__(self) -> None:
        self.vector = VectorRetriever()
        self.bm25 = BM25Retriever()
        self._build_bm25_index()

    def _build_bm25_index(self) -> None:
        all_docs = self.vector.collection.get(include=["documents", "metadatas"])
        chunks = [
            DocumentChunk(
                chunk_id=cid,
                doc_id=meta.get("source", ""),
                text=doc,
                metadata=meta,
            )
            for cid, doc, meta in zip(
                all_docs["ids"], all_docs["documents"], all_docs["metadatas"]
            )
        ]
        self.bm25.index(chunks)

    def retrieve(self, query: str) -> list[DocumentChunk]:
        v_results = self.vector.search(query, settings.VECTOR_TOP_K)
        b_results = self.bm25.search(query, settings.BM25_TOP_K)
        fused = _reciprocal_rank_fusion([v_results, b_results], k=settings.RRF_K)
        top = [c for c, _ in fused[: settings.RERANKER_TOP_K]]
        return top

    def retrieve_tickets(
        self, query: str, priority: str | None = None
    ) -> list[DocumentChunk]:
        where: dict = {"doc_type": "ticket"}
        if priority:
            where = {"$and": [{"doc_type": "ticket"}, {"priority": priority}]}

        ticket_query = f"support ticket incident {query}"
        v_results = self.vector.search(
            ticket_query, settings.VECTOR_TOP_K, where=where
        )
        b_results = [
            chunk
            for chunk in self.bm25.search(ticket_query, settings.BM25_TOP_K)
            if chunk.metadata.get("doc_type") == "ticket"
            and (not priority or chunk.metadata.get("priority") == priority)
        ]
        fused = _reciprocal_rank_fusion([v_results, b_results], k=settings.RRF_K)
        return [chunk for chunk, _ in fused[: settings.RERANKER_TOP_K]]
