from pathlib import Path
from typing import List
from app.config import settings
from ingestion.loaders import load_pdf, load_text_file
from ingestion.chunkers import chunk_text
from ingestion.cleaners import clean_text
from retrieval.embeddings import get_embedding_model

try:
    import chromadb

    HAS_CHROMADB = True
except ModuleNotFoundError:
    HAS_CHROMADB = False


def _flush(collection, ids, texts, embeds, metas) -> None:
    if not ids:
        return
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeds,
        metadatas=metas,
    )


def run_pipeline() -> None:
    if not HAS_CHROMADB:
        raise ModuleNotFoundError(
            "chromadb is required. Install it with: pip install chromadb"
        )
    client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    embedder = get_embedding_model()
    _ingest_directory(
        collection,
        embedder,
        settings.SOP_DIR,
        loader=load_pdf,
        prefix="sop",
    )
    _ingest_directory(
        collection,
        embedder,
        settings.IT_DOCS_DIR,
        loader=load_text_file,
        prefix="itdoc",
    )
    print(f"Ingestion complete. Collection size: {collection.count()}")


def _ingest_directory(
    collection,
    embedder,
    directory: Path,
    loader,
    prefix: str,
) -> None:
    if not directory.exists():
        return
    batch_ids: List[str] = []
    batch_texts: List[str] = []
    batch_embeds: List[List[float]] = []
    batch_metas: List[dict] = []
    for path in directory.glob("*"):
        for raw_text, meta in loader(path):
            text = clean_text(raw_text)
            page_suffix = f"_p{meta['page']}" if "page" in meta else ""
            chunks = chunk_text(
                text=text,
                chunk_id=f"{prefix}_{path.stem}{page_suffix}",
                metadata=meta,
            )
            for chunk in chunks:
                batch_ids.append(chunk.chunk_id)
                batch_texts.append(chunk.text)
                batch_embeds.append(embedder.encode(chunk.text).tolist())
                batch_metas.append(chunk.metadata)
        if len(batch_ids) >= 100:
            _flush(collection, batch_ids, batch_texts, batch_embeds, batch_metas)
            batch_ids, batch_texts, batch_embeds, batch_metas = [], [], [], []

    if batch_ids:
        _flush(collection, batch_ids, batch_texts, batch_embeds, batch_metas)
