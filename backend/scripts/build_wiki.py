"""
build_wiki.py

Lightweight "LLM-Wiki" inspired artifact for the Enterprise Knowledge Copilot.

This script queries the ChromaDB collection for top-k chunks per detected topic,
then uses the local Ollama LLM to write a small markdown wiki under data/wiki/.

It does NOT replace the live RAG pipeline. It is a related-work / future-enhancement
demonstration that shows awareness of Karpathy's LLM-Wiki pattern:

  https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Usage:
    python backend/scripts/build_wiki.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings
from retrieval.embeddings import embed_query

try:
    import chromadb
    import httpx

    HAS_CHROMADB = True
    HAS_HTTPX = True
except ModuleNotFoundError as exc:
    raise SystemExit(f"Missing dependency: {exc}. Run: pip install chromadb httpx")


WIKI_OUTPUT_DIR = settings.DATA_DIR / "wiki"
WIKI_INDEX = WIKI_OUTPUT_DIR / "index.md"
TOP_K_PER_TOPIC = 10
OLLAMA_MODEL = settings.OLLAMA_MODEL
OLLAMA_URL = settings.OLLAMA_BASE_URL


def _get_collection():
    client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIR))
    return client.get_collection(settings.CHROMA_COLLECTION)


def _discover_topics(collection) -> list[str]:
    """Return unique source documents as coarse 'topics' for the wiki."""
    all_metas = collection.get(include=["metadatas"])["metadatas"]
    topics = sorted({m.get("source", "unknown") for m in all_metas if m})
    return topics


def _fetch_chunks_for_topic(collection, topic: str, k: int = TOP_K_PER_TOPIC) -> list[dict]:
    """Retrieve top-k chunks that mention the topic/source."""
    results = collection.query(
        query_embeddings=[embed_query(topic)],
        n_results=k,
        where={"source": topic},
        include=["documents", "metadatas"],
    )
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "meta": meta})
    return chunks


def _ollama_generate(prompt: str, system: str | None = None) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 4096},
    }
    if system:
        payload["system"] = system
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as exc:
        return f"[WIKI GENERATION SKIPPED] Ollama unreachable: {exc}"


def _summarise_topic(topic: str, chunks: list[dict]) -> str:
    context = "\n\n".join(c["text"] for c in chunks[:5])
    prompt = (
        "You are an enterprise knowledge librarian. "
        "Write a concise markdown summary page (3-6 bullet points) for the topic below, "
        "using ONLY the provided context. "
        "Include a 'Sources' section listing the source filenames.\n\n"
        f"Topic: {topic}\n\nContext:\n{context}\n\nSummary:"
    )
    return _ollama_generate(
        prompt,
        system=(
            "Write clear, factual enterprise documentation summaries. "
            "Do not invent facts. Keep it short."
        ),
    )


def build_wiki() -> Path:
    collection = _get_collection()
    topics = _discover_topics(collection)
    WIKI_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "# Enterprise Knowledge Copilot — LLM-Wiki",
        "",
        "This wiki is auto-generated from ingested documents using the local Ollama model. "
        "It follows the pattern described by Karpathy (LLM-Wiki): a persistent, compounding "
        "knowledge layer that sits between raw sources and live retrieval.",
        "",
        "## Topics",
        "",
    ]

    for topic in topics:
        safe_name = topic.replace("/", "_").replace(" ", "_")
        page_path = WIKI_OUTPUT_DIR / f"{safe_name}.md"
        chunks = _fetch_chunks_for_topic(collection, topic)
        if not chunks:
            continue

        summary = _summarise_topic(topic, chunks)
        page_content = f"# {topic}\n\n{summary}\n"
        page_path.write_text(page_content, encoding="utf-8")

        rel_link = f"{safe_name}.md"
        index_lines.append(f"- [{topic}]({rel_link})")

    index_lines.append("")
    index_lines.append(f"Generated: {settings.APP_ENV} mode")
    WIKI_INDEX.write_text("\n".join(index_lines), encoding="utf-8")
    print(f"Wiki built at {WIKI_OUTPUT_DIR} ({len(topics)} pages)")
    return WIKI_INDEX


if __name__ == "__main__":
    build_wiki()
