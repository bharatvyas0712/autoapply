import logging
from typing import Any, Optional

import groq_client
import gemini_client

logger = logging.getLogger("career_copilot.llm")


def generate_json(prompt: str) -> Optional[Any]:
    """Tries Groq first (fast + free tier), falls back to Gemini if Groq
    isn't configured or the call fails. Returns None if neither is
    available/succeeds, so callers can fall back to deterministic logic."""
    if groq_client.is_available():
        result = groq_client.generate_json(prompt)
        if result is not None:
            return result
        logger.info("Groq call failed or returned nothing, falling back to Gemini")

    if gemini_client.is_available():
        return gemini_client.generate_json(prompt)

    return None


def is_available() -> bool:
    return groq_client.is_available() or gemini_client.is_available()