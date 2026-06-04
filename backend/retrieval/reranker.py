from __future__ import annotations
from typing import Sequence
from app.schemas import DocumentChunk
from app.config import settings


class Reranker:
    def __init__(self) -> None:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(settings.RERANKER_MODEL)

    def rerank(
        self, query: str, chunks: Sequence[DocumentChunk], top_k: int = 5
    ) -> list[DocumentChunk]:
        if not chunks:
            return []
        try:
            pairs = [(query, c.text) for c in chunks]
            scores = self._model.predict(pairs)
            scored = list(zip(chunks, scores.tolist()))
            scored.sort(key=lambda x: x[1], reverse=True)
            for chunk, score in scored[:top_k]:
                chunk.rerank_score = float(score)
            return [c for c, _ in scored[:top_k]]
        except Exception:
            return list(chunks)[:top_k]
