from typing import Dict, Any, List
from providers.groq_provider import GroqProvider

class ProviderManager:
    """
    Manages the active LLM provider. Groq is the only supported provider.
    """
    _active_provider = "groq"

    @staticmethod
    def get_active_provider() -> str:
        return ProviderManager._active_provider

    @staticmethod
    def set_active_provider(provider: str):
        valid = ["groq"]
        if provider.lower() in valid:
            ProviderManager._active_provider = provider.lower()
            return True
        return False

    @staticmethod
    async def run_chat(messages: List[Dict[str, str]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await GroqProvider.chat(messages, tools)