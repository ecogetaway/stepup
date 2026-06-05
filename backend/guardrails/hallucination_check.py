from app.schemas import Citation
from retrieval.embeddings import cosine_sim, embed_query
from app.config import settings


class HallucinationChecker:
    def check(self, answer: str, citations: list[Citation]) -> tuple[bool, float]:
        try:
            if not citations or not answer.strip():
                return True, 0.0

            answer_vec = embed_query(answer[:400])
            if not answer_vec:
                return True, 0.0

            similarities: list[float] = []
            for citation in citations[:2]:
                chunk_text = citation.chunk_text[:512].strip()
                if not chunk_text:
                    continue
                chunk_vec = embed_query(chunk_text)
                if not chunk_vec:
                    continue
                similarities.append(cosine_sim(answer_vec, chunk_vec))

            if not similarities:
                return True, 0.0

            best_sim = max(similarities)
            is_hallucinated = best_sim < settings.HALLUCINATION_SIMILARITY_THRESHOLD
            return is_hallucinated, best_sim
        except Exception:
            return False, 0.5
