from provider_manager import ProviderManager
from typing import List, Dict, Any

class LLMRouter:
    """
    Primary interface for forwarding conversations to active multi-LLM targets.
    """
    @staticmethod
    async def route_chat(messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        tool_list = tools or []
        return await ProviderManager.run_chat(messages, tool_list)
