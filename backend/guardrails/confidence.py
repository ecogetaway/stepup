from __future__ import annotations
from app.config import settings


class ConfidenceScorer:
    def score(
        self,
        citations: list,
        hallucination_flag: bool = False,
        coverage_score: float = 0.0,
    ) -> float:
        if not citations:
            return 0.0
        rerank_scores = [c.overlap_score or 0.0 for c in citations]
        divisor = min(len(rerank_scores), 3)
        rerank_signal = sum(rerank_scores[:3]) / divisor if divisor else 0.0
        count_signal = min(len(citations) / 5.0, 1.0)
        raw = 0.40 * rerank_signal + 0.25 * count_signal + 0.35 * coverage_score
        if hallucination_flag:
            raw *= 0.5
        return min(max(raw, 0.0), 1.0)

    def should_escalate(self, confidence: float) -> bool:
        return confidence < settings.CONFIDENCE_ESCALATION_THRESHOLD
