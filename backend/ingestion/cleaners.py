import re


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(
        r"\b[A-Z]{2,}\d{6,}\b",
        "[REDACTED-ID]",
        text,
    )
    return text
