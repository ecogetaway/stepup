from pathlib import Path
from typing import Iterator
from app.schemas import DocumentChunk

try:
    import pypdf  # type: ignore

    HAS_PYPDF = True
except ModuleNotFoundError:
    HAS_PYPDF = False


def load_pdf(path: Path) -> Iterator[tuple[str, dict]]:
    if not HAS_PYPDF:
        raise ModuleNotFoundError(
            "pypdf is required for PDF ingestion. Install it with: pip install pypdf"
        )
    reader = pypdf.PdfReader(str(path))
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            yield text, {
                "source": path.name,
                "source_url": f"docs/sops/{path.name}#page={i + 1}",
                "doc_type": "sop",
                "page": i + 1,
            }


def load_text_file(path: Path) -> Iterator[tuple[str, dict]]:
    text = path.read_text(encoding="utf-8")
    for para in text.split("\n\n"):
        if para.strip():
            yield para.strip(), {
                "source": path.name,
                "source_url": f"docs/it/{path.name}",
                "doc_type": "it_doc",
            }
