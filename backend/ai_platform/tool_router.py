from tool_executor import ToolExecutor
from typing import Dict, Any

class ToolRouter:
    """
    Routes execution calls directly to tool executors.
    """
    @staticmethod
    async def route_run(name: str, arguments: dict, conversation_id: int = 1) -> dict:
        return await ToolExecutor.execute(name, arguments, conversation_id)
