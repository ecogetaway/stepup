from __future__ import annotations

import math

from app.schemas import DocumentChunk


def normalise_overlap_score(score: float | None) -> float:
    if score is None:
        return 0.0
    if 0.0 <= score <= 1.0:
        return float(score)
    return float(1.0 / (1.0 + math.exp(-score)))


def chunk_overlap_score(chunk: DocumentChunk, rank: int) -> float:
    if chunk.rerank_score is not None and chunk.rerank_score > 0:
        return normalise_overlap_score(chunk.rerank_score)
    if chunk.bm25_score is not None and chunk.bm25_score > 0:
        return normalise_overlap_score(chunk.bm25_score)
    return max(0.55, 0.92 - (rank * 0.08))
