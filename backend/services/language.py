from __future__ import annotations

import logging

from agents.llm import LLM_FAILURE_PREFIX, call_llm

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"hi": "Hindi"}


def detect_language(text: str) -> str:
    """Return 'hi' if the text contains meaningful Devanagari script, else 'en'."""
    if not text:
        return "en"
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return "en"
    devanagari = sum(1 for ch in letters if "\u0900" <= ch <= "\u097f")
    return "hi" if devanagari / len(letters) >= 0.10 else "en"


def _translate(text: str, instruction: str) -> str | None:
    result = call_llm(prompt=text, system_prompt=instruction)
    if not result or result.startswith(LLM_FAILURE_PREFIX):
        logger.warning("Translation failed; falling back to original text")
        return None
    return result.strip()


def translate_to_english(text: str) -> str | None:
    return _translate(
        text,
        "Translate the user's message to English. Preserve technical terms "
        "(e.g. Kafka, Docker, VPN, P1) exactly as written. "
        "Return ONLY the English translation, nothing else.",
    )


def translate_from_english(text: str, lang: str) -> str | None:
    language_name = SUPPORTED_LANGUAGES.get(lang)
    if not language_name:
        return None
    return _translate(
        text,
        f"Translate the following answer into {language_name}. Keep technical "
        "terms, command names, and file names in English. Preserve markdown "
        "formatting. Return ONLY the translation, nothing else.",
    )
