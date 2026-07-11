from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from service import MemoryService

router = APIRouter(prefix="/api/memory", tags=["Long-Term Memory Agent"])

class StoreRequest(BaseModel):
    user_id: int
    memory_type: str
    key: str
    value: Dict[str, Any]

class FeedbackRequest(BaseModel):
    user_id: int
    target_id: int
    target_type: str
    action: str  # like, dislike, edit, approve
    comment: Optional[str] = None

@router.post("/store")
async def store_memory(req: StoreRequest):
    """Stores a fact or execution trace into persistent memory."""
    try:
        mem_id = await MemoryService.store_memory(req.user_id, req.memory_type, req.key, req.value)
        return {"success": True, "memory_id": mem_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_memory(user_id: int, query: str, memory_type: Optional[str] = None, top_k: int = 5):
    """Searches long term database using vector cosine comparisons."""
    try:
        results = await MemoryService.search_memory(user_id, query, memory_type, top_k)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company/{company}")
async def get_company_history(company: str, user_id: int):
    """Retrieves previous interaction logs with a company."""
    try:
        history = await MemoryService.get_company_history(user_id, company)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/application-history")
async def get_application_history(user_id: int):
    """Retrieves previous job submissions and outcomes."""
    try:
        history = await MemoryService.get_application_history(user_id)
        return {"success": True, "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_recommendations(user_id: int):
    """Generates personalized study tips and target titles."""
    try:
        recs = await MemoryService.get_recommendations(user_id)
        return {"success": True, "data": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def post_feedback(req: FeedbackRequest):
    """Logs explicit reactions (likes/dislikes) to reinforce answers."""
    try:
        await MemoryService.save_feedback(req.user_id, req.target_id, req.target_type, req.action, req.comment)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(user_id: int):
    """Compiles learning success metrics."""
    try:
        stats = await MemoryService.get_statistics(user_id)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumes")
async def get_resume_versions(user_id: int):
    """Retrieves registered resume versions."""
    try:
        data = await MemoryService.get_resume_versions(user_id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
