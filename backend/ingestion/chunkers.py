from typing import List
from app.schemas import DocumentChunk


def chunk_text(
    text: str,
    chunk_id: str,
    metadata: dict,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        chunks.append(
            DocumentChunk(
                chunk_id=f"{chunk_id}_chunk_{idx}",
                doc_id=chunk_id,
                text=chunk_text,
                metadata=metadata,
            )
        )
        start = end - overlap
        idx += 1
    return chunks
