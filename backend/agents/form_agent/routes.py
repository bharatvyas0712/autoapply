from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from service import FormService
from agent import FormFillingAgent

router = APIRouter(prefix="/api/form", tags=["Form Filling & QA Agent"])

class AnalyzeRequest(BaseModel):
    user_id: int
    job_id: int
    dom_structure: List[Dict[str, Any]]
    profile: Dict[str, Any]
    job_details: Dict[str, Any]
    resume_path: str
    cover_letter_path: str = ""

class CoverLetterRequest(BaseModel):
    user_id: int
    job_id: int
    profile: Dict[str, Any]
    job_details: Dict[str, Any]
    length: str = "medium"

class ApproveRequest(BaseModel):
    user_response: str = None

class AddReviewItemRequest(BaseModel):
    user_id: int
    job_id: int
    question_text: str
    proposed_answer: str = ""
    confidence: float = 0.0

@router.post("/analyze")
async def analyze_form(req: AnalyzeRequest):
    """Analyzes form DOM and prepares filling mapping & review checks."""
    try:
        res = await FormFillingAgent.analyze_and_generate(
            user_id=req.user_id,
            job_id=req.job_id,
            dom_structure=req.dom_structure,
            profile=req.profile,
            job_details=req.job_details,
            resume_path=req.resume_path,
            cover_letter_path=req.cover_letter_path
        )
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-cover-letter")
async def generate_cover_letter(req: CoverLetterRequest):
    """Generates tailored cover letter and saves to DB."""
    try:
        content = await FormService.generate_cover_letter(
            req.user_id, req.job_id, req.profile, req.job_details, req.length
        )
        return {"success": True, "cover_letter": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/review")
async def get_review_queue(user_id: int):
    """Gets all active items waiting in Review Queue."""
    items = await FormService.get_review_items(user_id)
    return {"success": True, "data": items}

@router.post("/review/add")
async def add_review_item(req: AddReviewItemRequest):
    """Pushes a single question onto the Review Queue (used by the live browser automation)."""
    review_id = await FormService.add_review_item(
        req.user_id, req.job_id, req.question_text, req.proposed_answer, req.confidence
    )
    return {"success": True, "review_id": review_id}

@router.get("/review/{id}")
async def get_review_item(id: int):
    """Gets a single Review Queue item — used by the browser automation to poll for a resolution."""
    item = await FormService.get_review_item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found.")
    return {"success": True, "data": item}

@router.post("/review/{id}/approve")
async def approve_item(id: int, req: ApproveRequest = ApproveRequest()):
    """Approves a queued question, optionally saving an edited/user-provided answer."""
    success = await FormService.approve_review_item(id, req.user_response)
    return {"success": success}

@router.post("/review/{id}/reject")
async def reject_item(id: int):
    """Rejects a queued question."""
    success = await FormService.reject_review_item(id)
    return {"success": success}

@router.get("/history")
async def get_history(user_id: int, limit: int = 50):
    """Gets historical QA database log."""
    data = await FormService.get_history(user_id, limit)
    return {"success": True, "data": data}

@router.get("/cover-letters")
async def get_cover_letters(user_id: int):
    """Retrieves all generated cover letters."""
    data = await FormService.get_cover_letters(user_id)
    return {"success": True, "data": data}
