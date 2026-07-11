import json
import logging
import re
from typing import Any, Optional

from config import settings

logger = logging.getLogger("form_agent.groq")

_client = None
_init_failed = False


def _get_client():
    global _client, _init_failed
    if _client is not None or _init_failed:
        return _client
    if not settings.GROQ_API_KEY:
        _init_failed = True
        return None
    try:
        # Groq's API is OpenAI-compatible, so the official `openai` SDK
        # works fine pointed at Groq's base URL.
        from openai import OpenAI
        _client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    except Exception:
        logger.exception("Failed to initialize Groq client")
        _init_failed = True
        _client = None
    return _client


def _extract_json(text: str) -> Optional[Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(json)?", "", text).rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def generate_json(prompt: str) -> Optional[Any]:
    """Calls Groq and parses a JSON object/array from the response.
    Returns None if no API key is configured or the call/parse fails,
    so callers can fall back to deterministic template logic."""
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return _extract_json(response.choices[0].message.content)
    except Exception:
        logger.exception("Groq generation failed")
        return None


def is_available() -> bool:
    return _get_client() is not None