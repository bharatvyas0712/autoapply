import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from config import settings
from database import init_db, AsyncSessionLocal, JobSearchHistory, SearchSession
from sqlalchemy.future import select
from sqlalchemy import desc
from agent import JobSearchAgent
from scheduler import job_scheduler

app = FastAPI(
    title="AutoJobApply - Job Search Agent",
    description="AI-powered asynchronous job search agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()
    # Don't start scheduler automatically in tests/dev unless specified, but for prod we would:
    # job_scheduler.start()
    
@app.on_event("shutdown")
async def shutdown_event():
    job_scheduler.stop()

@app.get("/health")
async def health():
    return {"success": True, "message": "Job Search Agent running ✅"}

class SearchRequest(BaseModel):
    user_id: int
    user_profile: Dict[str, Any]
    filters: Dict[str, Any] = {}

@app.post("/api/search/start")
async def start_search():
    """Starts the background scheduler for continuous searches."""
    job_scheduler.start()
    return {"success": True, "message": "Background search scheduler started."}

@app.post("/api/search/stop")
async def stop_search():
    """Stops the background scheduler."""
    job_scheduler.stop()
    return {"success": True, "message": "Background search scheduler stopped."}

@app.post("/api/search/run-once")
async def run_once(req: SearchRequest, background_tasks: BackgroundTasks):
    """
    Triggers an immediate background search for a single user.
    """
    # Run async in background
    background_tasks.add_task(
        JobSearchAgent.run_search_for_user,
        user_profile=req.user_profile,
        search_filters=req.filters
    )
    return {"success": True, "message": f"Search queued for user {req.user_id}."}

@app.get("/api/search/results")
async def get_results(user_id: int, limit: int = 50, offset: int = 0):
    """Returns normalized job results from the database."""
    async with AsyncSessionLocal() as db:
        stmt = select(JobSearchHistory).where(JobSearchHistory.user_id == user_id).order_by(desc(JobSearchHistory.match_score), desc(JobSearchHistory.created_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        return {"success": True, "data": [j.to_dict() for j in jobs]}

@app.get("/api/search/history")
async def get_history(user_id: int):
    """Returns the search sessions history."""
    async with AsyncSessionLocal() as db:
        stmt = select(SearchSession).where(SearchSession.user_id == user_id).order_by(desc(SearchSession.started_at)).limit(20)
        result = await db.execute(stmt)
        sessions = result.scalars().all()
        return {"success": True, "data": [s.to_dict() for s in sessions]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.AGENT_PORT, reload=False)
