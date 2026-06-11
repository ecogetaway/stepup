from __future__ import annotations

from app.schemas import Citation, SlaStatus
from retrieval.scoring import chunk_overlap_score
from services.sla import compute_sla_state


def sla_from_metadata(metadata: dict) -> SlaStatus | None:
    if metadata.get("doc_type") != "ticket":
        return None

    created_at = metadata.get("created_at")
    priority = metadata.get("priority", "")
    status = metadata.get("status", "")
    if not created_at:
        return None

    sla = compute_sla_state(created_at, priority, status)
    if sla is None:
        return None

    return SlaStatus(
        state=sla.state,
        due_at=sla.sla_due_at.isoformat(timespec="seconds"),
        remaining_minutes=sla.remaining_minutes,
        elapsed_pct=sla.elapsed_pct,
    )


def build_citation_from_chunk(chunk, rank: int) -> Citation:
    metadata = chunk.metadata if hasattr(chunk, "metadata") else {}
    return Citation(
        source_title=metadata.get("source", "unknown"),
        source_url=metadata.get("source_url", ""),
        chunk_text=chunk.text[:200],
        full_text=chunk.text[:4000],
        overlap_score=chunk_overlap_score(chunk, rank),
        doc_type=metadata.get("doc_type", "unknown"),
        sla=sla_from_metadata(metadata),
    )
