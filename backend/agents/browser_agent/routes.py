from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from service import BrowserService
from state_manager import state_manager

router = APIRouter(prefix="/api/browser", tags=["Browser Application Agent"])

class StartSessionRequest(BaseModel):
    user_id: int
    browser_type: str = "chromium"

class ApplyRequest(BaseModel):
    user_id: int
    session_id: str
    job_id: int
    job_url: str
    form_data: Dict[str, Any]
    resume_path: str
    cover_letter_path: str = ""

@router.post("/start")
async def start_session(req: StartSessionRequest):
    """Starts a persistent browser session and returns a session ID."""
    try:
        session_id = await BrowserService.start_session(req.user_id, req.browser_type)
        return {"success": True, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_session(session_id: str):
    """Stops an active browser session."""
    try:
        await BrowserService.stop_session(session_id)
        return {"success": True, "message": "Browser session stopped successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply/{job_id}")
async def apply_job(job_id: int, req: ApplyRequest, background_tasks: BackgroundTasks):
    """Triggers an autonomous application submission in the background."""
    background_tasks.add_task(
        BrowserService.apply_to_job,
        user_id=req.user_id,
        session_id=req.session_id,
        job_id=job_id,
        job_url=req.job_url,
        form_data=req.form_data,
        resume_path=req.resume_path,
        cover_letter_path=req.cover_letter_path
    )
    return {"success": True, "message": f"Browser application process queued for job {job_id}."}

@router.post("/pause/{job_id}")
async def pause_apply(job_id: int, reason: str = "manual"):
    """Pauses browser execution (e.g. for CAPTCHA/Login)."""
    state = state_manager.get(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active execution state not found.")
    state.pause(reason)
    return {"success": True, "message": f"Execution paused. Reason: {reason}"}

@router.post("/resume/{job_id}")
async def resume_apply(job_id: int):
    """Resumes browser execution after solving CAPTCHA/Login."""
    state = state_manager.get(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active execution state not found.")
    state.resume()
    return {"success": True, "message": "Execution resumed."}

@router.get("/status")
async def get_status(job_id: int):
    """Returns the current execution state for a job."""
    state = state_manager.get(job_id)
    if not state:
        return {"success": True, "status": "idle", "message": "No active execution."}
    return {"success": True, "data": state.to_dict()}

@router.get("/logs")
async def get_logs(session_id: str, limit: int = 100):
    """Retrieves execution logs for the given browser session."""
    logs = await BrowserService.get_logs(session_id, limit)
    return {"success": True, "data": logs}

@router.get("/screenshots")
async def get_screenshots(execution_id: int):
    """Retrieves screenshots saved during execution."""
    screenshots = await BrowserService.get_screenshots(execution_id)
    return {"success": True, "data": screenshots}
