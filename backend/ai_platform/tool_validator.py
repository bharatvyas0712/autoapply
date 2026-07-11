from tool_registry import ToolRegistry
from typing import Dict, Any

class ToolValidator:
    """
    Checks incoming tool call arguments against target schemas.
    """
    
    @staticmethod
    def validate(name: str, arguments: dict) -> bool:
        tool = ToolRegistry.get_tool(name)
        if not tool:
            return False
            
        definition = tool.get_definition()
        params = definition.get("parameters", {})
        required = params.get("required", [])
        
        for req in required:
            if req not in arguments:
                return False
                
        return True
