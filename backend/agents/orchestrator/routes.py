from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from service import OrchestratorService

router = APIRouter(prefix="/api/orchestrator", tags=["Multi-Agent Orchestrator"])

class StartRequest(BaseModel):
    user_id: int
    resume_path: str = ""

@router.post("/start")
async def start_workflow(req: StartRequest):
    """Starts a new multi-agent orchestrator workflow session."""
    try:
        session_id = await OrchestratorService.start_workflow(req.user_id, req.resume_path)
        return {"success": True, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
async def pause_workflow(session_id: int, reason: str = "manual"):
    """Pauses a running orchestrator workflow session."""
    success = await OrchestratorService.pause_workflow(session_id, reason)
    return {"success": success}

@router.post("/resume")
async def resume_workflow(session_id: int):
    """Resumes a paused orchestrator workflow session."""
    success = await OrchestratorService.resume_workflow(session_id)
    return {"success": success}

@router.post("/stop")
async def stop_workflow(session_id: int):
    """Stops an active orchestrator workflow session."""
    success = await OrchestratorService.stop_workflow(session_id)
    return {"success": success}

@router.get("/state")
async def get_state(session_id: int):
    """Gets the current shared state dictionary of a workflow."""
    return await OrchestratorService.get_state(session_id)

@router.get("/history")
async def get_history(session_id: int):
    """Retrieves step execution histories for a session."""
    data = await OrchestratorService.get_history(session_id)
    return {"success": True, "data": data}

@router.get("/graph")
async def get_graph():
    """Generates and returns the LangGraph configuration in Mermaid string layout."""
    mermaid = OrchestratorService.get_mermaid_graph()
    return {"success": True, "graph": mermaid}

@router.get("/graph/png")
async def get_graph_png():
    """Returns the compiled LangGraph flow diagram as a PNG image stream."""
    png_bytes = OrchestratorService.get_png_graph()
    if not png_bytes:
        raise HTTPException(status_code=400, detail="PNG rendering not supported by environment dependencies.")
    return Response(content=png_bytes, media_type="image/png")