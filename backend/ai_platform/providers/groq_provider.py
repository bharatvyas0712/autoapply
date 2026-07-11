import json
import logging
from typing import Dict, Any, List

from config import settings

logger = logging.getLogger("ai_platform.groq")

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


def _to_openai_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts this platform's tool definitions ({name, description, parameters})
    into the OpenAI/Groq function-calling tool schema."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def _sanitize_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Groq's API (like OpenAI's) requires every assistant message with
    tool_calls to include a call id + function shape, immediately followed
    by matching 'tool' role message(s) with the result. Properly-built
    tool turns (constructed within the same request, with real ids) are
    kept as-is. But this app's *persisted* conversation history stores
    tool calls in a simplified legacy shape (no id) with no matching tool
    result message - those get stripped down to plain text so they don't
    violate the schema."""
    clean = []
    for m in messages:
        role = m.get("role")
        if role == "assistant" and m.get("tool_calls"):
            tool_calls = m["tool_calls"]
            well_formed = all(
                isinstance(tc, dict) and "id" in tc and "function" in tc
                for tc in tool_calls
            )
            if well_formed:
                clean.append({
                    "role": "assistant",
                    "content": m.get("content") or "",
                    "tool_calls": tool_calls,
                })
            else:
                clean.append({
                    "role": "assistant",
                    "content": m.get("content") or "(requested a tool call)",
                })
        elif role == "tool":
            clean.append({
                "role": "tool",
                "tool_call_id": m.get("tool_call_id"),
                "content": m.get("content", ""),
            })
        else:
            clean.append({"role": role, "content": m.get("content", "")})
    return clean


class GroqProvider:
    @staticmethod
    async def chat(messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        client = _get_client()
        if client is None:
            return {
                "role": "assistant",
                "content": "Groq is not configured. Set GROQ_API_KEY in your .env file.",
            }

        try:
            kwargs: Dict[str, Any] = {
                "model": settings.GROQ_MODEL,
                "messages": _sanitize_history(messages),
            }
            if tools:
                kwargs["tools"] = _to_openai_tools(tools)
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0].message

            result: Dict[str, Any] = {
                "role": "assistant",
                "content": choice.content or "",
            }

            if choice.tool_calls:
                parsed_calls = []
                for call in choice.tool_calls:
                    try:
                        args = json.loads(call.function.arguments)
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    parsed_calls.append({"id": call.id, "name": call.function.name, "arguments": args})
                result["tool_calls"] = parsed_calls

            return result
        except Exception:
            logger.exception("Groq chat call failed")
            return {
                "role": "assistant",
                "content": "Sorry, the Groq request failed. Please try again.",
            }