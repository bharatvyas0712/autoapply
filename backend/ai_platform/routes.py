from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, List
from service import AIPlatformService
from streaming import SSEStreamManager
from mcp_server import mcp_router

router = APIRouter()
router.include_router(mcp_router)

class ChatRequest(BaseModel):
    conversation_id: int
    message: str
    stream: bool = False

class RunToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]
    conversation_id: int

class SwitchRequest(BaseModel):
    provider_name: str

@router.post("/api/llm/chat")
async def chat(req: ChatRequest):
    """Unified chat endpoint supporting tool discovery & streaming fallbacks."""
    try:
        res = await AIPlatformService.chat(req.conversation_id, req.message)
        if req.stream:
            content = res.get("content", "Executing tools...")
            return StreamingResponse(SSEStreamManager.generate_chunks(content), media_type="text/event-stream")
        return {"success": True, "response": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/tools/run")
async def run_tool(req: RunToolRequest):
    """Executes registered tools (Resume parser, email sender, searcher)."""
    try:
        res = await AIPlatformService.run_tool(req.name, req.arguments, req.conversation_id)
        return {"success": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tools")
async def get_tools():
    """Gets registered tool definitions and JSON schemas."""
    return {"success": True, "tools": AIPlatformService.get_tools()}

@router.get("/api/providers")
async def get_providers(user_id: int = 1):
    """Gets all Multi-LLM providers and their activation states."""
    data = await AIPlatformService.get_providers(user_id)
    return {"success": True, "data": data}

@router.post("/api/providers/switch")
async def switch_provider(req: SwitchRequest):
    """Switches LLM routing (OpenAI, Anthropic, Gemini, Ollama)."""
    success = await AIPlatformService.switch_provider(req.provider_name)
    return {"success": success}

@router.get("/api/conversations")
async def get_conversations(user_id: int = 1):
    """Gets list of all previous conversations."""
    data = await AIPlatformService.get_conversations(user_id)
    return {"success": True, "data": data}
