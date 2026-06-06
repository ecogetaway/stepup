from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import chromadb

    HAS_CHROMADB = True
except ModuleNotFoundError:
    HAS_CHROMADB = False


def _collection_count() -> int | None:
    if not HAS_CHROMADB:
        return None

    persist_dir = Path(settings.CHROMA_PERSIST_DIR)
    if not persist_dir.exists():
        return 0

    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        collection = client.get_collection(settings.CHROMA_COLLECTION)
    except Exception:
        return 0

    return collection.count()


def ensure_demo_data_ready() -> None:
    """Generate sample docs and ingest Chroma if the vector store is empty."""
    settings.SOP_DIR.mkdir(parents=True, exist_ok=True)
    settings.TICKET_CSV.parent.mkdir(parents=True, exist_ok=True)
    settings.IT_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

    sop_files = list(settings.SOP_DIR.glob("*.pdf"))
    if not sop_files:
        logger.info("Generating sample SOP PDFs for demo data")
        from scripts.generate_sample_data import main as generate_sops

        generate_sops()

    if not settings.TICKET_CSV.exists():
        logger.info("Generating sample ticket CSV for demo data")
        from scripts.generate_tickets import main as generate_tickets

        generate_tickets()

    doc_count = _collection_count()
    if doc_count is None:
        logger.warning("chromadb unavailable; skipping auto-ingest")
        return

    if doc_count > 0:
        from ingestion.pipeline import count_ticket_chunks, ingest_tickets_only

        ticket_count = count_ticket_chunks()
        if ticket_count == 0 and settings.TICKET_CSV.exists():
            logger.info(
                "Chroma has %s documents but no ticket chunks; ingesting tickets",
                doc_count,
            )
            ingest_tickets_only()
        else:
            logger.info(
                "Chroma collection ready with %s documents (%s ticket chunks)",
                doc_count,
                ticket_count,
            )
        return

    logger.info("Chroma collection empty; running ingestion")
    from ingestion.pipeline import run_pipeline

    run_pipeline()
