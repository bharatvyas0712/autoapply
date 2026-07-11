import json
import logging
import re
from typing import Any, Optional

from config import settings

logger = logging.getLogger("career_copilot.gemini")

_model = None
_init_failed = False


def _get_model():
    global _model, _init_failed
    if _model is not None or _init_failed:
        return _model
    if not settings.GEMINI_API_KEY:
        _init_failed = True
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(settings.GEMINI_MODEL)
    except Exception:
        logger.exception("Failed to initialize Gemini client")
        _init_failed = True
        _model = None
    return _model


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
    """Calls Gemini and parses a JSON object/array from the response.
    Returns None if no API key is configured or the call/parse fails,
    so callers can fall back to deterministic logic."""
    model = _get_model()
    if model is None:
        return None
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return _extract_json(response.text)
    except Exception:
        logger.exception("Gemini generation failed")
        return None


def is_available() -> bool:
    return _get_model() is not None
