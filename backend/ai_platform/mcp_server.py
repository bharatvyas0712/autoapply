from fastapi import APIRouter, HTTPException
from tool_registry import ToolRegistry
from tool_executor import ToolExecutor
from typing import Dict, Any

mcp_router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])

@mcp_router.get("/tools")
async def mcp_discover_tools():
    """MCP Discovery: Returns list of registered tools and parameters."""
    tools = ToolRegistry.get_all_tools()
    return {"tools": tools}

@mcp_router.post("/tools/call")
async def mcp_call_tool(req: Dict[str, Any]):
    """MCP Invocation: Executes a tool and returns formatted output."""
    name = req.get("name")
    arguments = req.get("arguments", {})
    
    if not name:
        raise HTTPException(status_code=400, detail="Tool name parameter required.")
        
    res = await ToolExecutor.execute(name, arguments)
    return {"result": res}
