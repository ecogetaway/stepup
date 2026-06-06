from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)

LLM_FAILURE_PREFIX = "[DEMO FALLBACK]"

try:
    import httpx

    HAS_HTTPX = True
except ModuleNotFoundError:
    HAS_HTTPX = False


def _failure(message: str) -> str:
    return f"{LLM_FAILURE_PREFIX} {message}"


def _call_ollama(prompt: str, system_prompt: str | None = None) -> str:
    if not HAS_HTTPX:
        return _failure("httpx not installed. Install it to enable live LLM calls.")

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    if system_prompt:
        payload["system"] = system_prompt

    timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("response", "").strip()
            if not answer:
                return _failure("Empty response from Ollama.")
            return answer
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
        return _failure(
            f"Ollama unreachable at {settings.OLLAMA_BASE_URL}. "
            f"Start Ollama or check the URL. Error: {exc}"
        )


def _call_openai(prompt: str, system_prompt: str | None = None) -> str:
    if not HAS_HTTPX:
        return _failure("httpx not installed. Install it to enable live LLM calls.")
    if not settings.OPENAI_API_KEY:
        return _failure("OPENAI_API_KEY is not set.")

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            answer = (data["choices"][0]["message"].get("content") or "").strip()
            if not answer:
                return _failure("Empty response from OpenAI.")
            return answer
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return _failure(
            f"OpenAI unreachable for model {settings.OPENAI_MODEL}. Error: {exc}"
        )


def _call_openrouter(prompt: str, system_prompt: str | None = None) -> str:
    if not HAS_HTTPX:
        return _failure("httpx not installed. Install it to enable live LLM calls.")
    if not settings.OPENROUTER_API_KEY:
        return _failure("OPENROUTER_API_KEY is not set.")

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_HTTP_REFERER,
        "X-Title": settings.APP_NAME,
    }

    timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0].get("message", {})
            answer = (message.get("content") or "").strip()
            if not answer:
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                if isinstance(reasoning, str):
                    answer = reasoning.strip()
            if not answer:
                return _failure("Empty response from OpenRouter.")
            return answer
    except Exception as exc:
        logger.warning("OpenRouter call failed: %s", exc)
        return _failure(
            f"OpenRouter unreachable for model {settings.OPENROUTER_MODEL}. Error: {exc}"
        )


def call_llm(prompt: str, system_prompt: str | None = None) -> str:
    if settings.SKIP_LLM:
        return _failure("LLM synthesis disabled (SKIP_LLM=true).")

    provider = settings.LLM_PROVIDER.strip().lower()
    if provider in {"none", "retrieval"}:
        return _failure("LLM synthesis disabled for retrieval-only mode.")
    if provider == "openai":
        return _call_openai(prompt, system_prompt=system_prompt)
    if provider == "openrouter":
        return _call_openrouter(prompt, system_prompt=system_prompt)
    return _call_ollama(prompt, system_prompt=system_prompt)
