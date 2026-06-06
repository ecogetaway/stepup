import csv
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


def load_tickets_csv(path: Path) -> Iterator[tuple[str, dict]]:
    if not path.exists():
        return

    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            ticket_id = (row.get("id") or "").strip()
            priority = (row.get("priority") or "").strip()
            category = (row.get("category") or "").strip()
            subject = (row.get("subject") or "").strip()
            description = (row.get("description") or "").strip()
            status = (row.get("status") or "").strip()
            created_at = (row.get("created_at") or "").strip()

            if not ticket_id or not subject:
                continue

            text = (
                f"Ticket {ticket_id} | {priority} | {category} | {subject}\n"
                f"Status: {status}\n"
                f"Created: {created_at}\n"
                f"{description}"
            )
            yield text, {
                "source": ticket_id,
                "source_url": f"tickets/{ticket_id}",
                "doc_type": "ticket",
                "priority": priority,
                "category": category,
                "status": status,
                "created_at": created_at,
            }
