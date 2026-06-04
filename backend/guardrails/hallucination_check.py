from app.schemas import Citation
from retrieval.embeddings import cosine_sim, embed_query
from app.config import settings


class HallucinationChecker:
    def check(self, answer: str, citations: list[Citation]) -> tuple[bool, float]:
        if not citations:
            return True, 0.0
        answer_vec = embed_query(answer)
        best_sim = max(
            cosine_sim(answer_vec, embed_query(c.chunk_text[:512])) for c in citations
        )
        is_hallucinated = best_sim < settings.HALLUCINATION_SIMILARITY_THRESHOLD
        return is_hallucinated, best_sim
