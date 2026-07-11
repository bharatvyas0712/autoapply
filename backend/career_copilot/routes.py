from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from service import CareerCopilotService

router = APIRouter(prefix="/api/copilot", tags=["AI Career Copilot"])

class ResumeOptimizeRequest(BaseModel):
    user_id: int
    resume_text: str
    keywords: List[str]

class AtsRequest(BaseModel):
    resume_text: str
    job_description: str

class LinkedinRequest(BaseModel):
    skills: List[str]
    target_role: str

class MockRequest(BaseModel):
    user_id: int
    interview_type: str

class SalaryRequest(BaseModel):
    user_id: int
    role: str
    location: str

class SkillGapRequest(BaseModel):
    current_skills: List[str]
    target_skills: List[str]

class RoadmapRequest(BaseModel):
    user_id: int
    current_role: str
    target_role: str

@router.post("/resume-optimize")
async def optimize_resume(req: ResumeOptimizeRequest):
    """Suggests action verbs, missing skills and updates layout."""
    try:
        res = await CareerCopilotService.optimize_resume(req.user_id, req.resume_text, req.keywords)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ats-score")
async def get_ats_score(req: AtsRequest):
    """Calculates overall ATS score and matching densities."""
    try:
        res = CareerCopilotService.get_ats_score(req.resume_text, req.job_description)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/linkedin-optimize")
async def optimize_linkedin(req: LinkedinRequest):
    """Generates optimized recruiter-friendly headlines and summaries."""
    try:
        res = CareerCopilotService.optimize_linkedin(req.skills, req.target_role)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mock-interview")
async def start_mock_interview(req: MockRequest):
    """Spawns mock QAs for the targeted interview type."""
    try:
        res = await CareerCopilotService.start_mock_interview(req.user_id, req.interview_type)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/salary")
async def get_salary(req: SalaryRequest):
    """Calculates expected compensation ranges."""
    try:
        res = await CareerCopilotService.get_salary_prediction(req.user_id, req.role, req.location)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skill-gap")
async def get_skill_gap(req: SkillGapRequest):
    """Compares skills and flags learning lists."""
    try:
        res = CareerCopilotService.get_skill_gap(req.current_skills, req.target_skills)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/career-roadmap")
async def get_roadmap(req: RoadmapRequest):
    """Calculates 6m, 12m and 24m developmental goals."""
    try:
        res = await CareerCopilotService.get_career_roadmap(req.user_id, req.current_role, req.target_role)
        return {"success": True, "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_analytics(user_id: int):
    """Compiles overall career score progress trends."""
    return {
        "success": True,
        "data": {
            "ats_score_trend": [65.0, 72.0, 84.5],
            "resume_performance": "High Match Density",
            "interview_rate": 28.5
        }
    }
