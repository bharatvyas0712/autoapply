from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List
from service import MatchingService

router = APIRouter(prefix="/api/matching", tags=["Job Matching Agent"])

class RunRequest(BaseModel):
    user_id: int
    user_profile: Dict[str, Any]
    jobs: List[Dict[str, Any]]

@router.post("/run")
async def run_matching(req: RunRequest, background_tasks: BackgroundTasks):
    """Runs semantic matching in the background for a batch of jobs."""
    background_tasks.add_task(
        MatchingService.run_matching,
        user_id=req.user_id,
        user_profile=req.user_profile,
        jobs=req.jobs
    )
    return {"success": True, "message": f"Matching started for {len(req.jobs)} jobs."}

@router.post("/job/{job_id}")
async def run_single_job_matching(job_id: int, req: RunRequest):
    """Runs semantic matching synchronously for a single job."""
    res = await MatchingService.run_matching(req.user_id, req.user_profile, req.jobs)
    return res

@router.get("/results")
async def get_results(user_id: int, limit: int = 50, offset: int = 0):
    data = await MatchingService.get_results(user_id, limit, offset)
    return {"success": True, "data": data}

@router.get("/top")
async def get_top_recommendations(user_id: int, limit: int = 5):
    data = await MatchingService.get_top_recommendations(user_id, limit)
    return {"success": True, "data": data}

@router.get("/skill-gap")
async def get_skill_gap(user_id: int, limit: int = 10):
    data = await MatchingService.get_skill_gap(user_id, limit)
    return {"success": True, "data": data}

@router.get("/statistics")
async def get_statistics(user_id: int):
    data = await MatchingService.get_statistics(user_id)
    return {"success": True, "data": data}
