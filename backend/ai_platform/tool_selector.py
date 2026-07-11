from tool_registry import ToolRegistry
from typing import List, Dict, Any

class ToolSelector:
    """
    Scans a prompt and selects the subset of tools to supply to the LLM context.
    """
    
    @staticmethod
    def select_tools(user_prompt: str) -> List[Dict[str, Any]]:
        # Basic filter to shrink context window
        prompt = user_prompt.lower()
        all_tools = ToolRegistry.get_all_tools()
        
        selected = []
        for tool in all_tools:
            name = tool["name"]
            # Expose everything or apply rules
            selected.append(tool)
        return selected
