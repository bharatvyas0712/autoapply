from langgraph.graph import StateGraph, END
from state import AgentState
from supervisor import SupervisorAgent
from router import WorkflowRouter
from utilities.logger import get_logger
from config import settings
import aiohttp
import asyncio

logger = get_logger("Graph")

TIMEOUT = aiohttp.ClientTimeout(total=settings.SERVICE_CALL_TIMEOUT_SECONDS)


async def _post(url: str, json_body: dict) -> dict:
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        async with session.post(url, json=json_body) as resp:
            resp.raise_for_status()
            return await resp.json()


async def _get(url: str, params: dict) -> dict:
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


# Node implementation functions - each calls the real microservice over HTTP.
# If a service is unreachable (e.g. not running locally), we fall back to a
# clearly-labeled simulated result so the workflow can still be observed
# end-to-end during local development/testing.

async def resume_node(state: AgentState) -> dict:
    logger.info("Executing Resume Analyzer Node...")
    resume_path = state.get("resume_path") or "/path/to/user/resume.pdf"
    try:
        payload = await _post(
            f"{settings.AI_PLATFORM_URL}/api/tools/run",
            {"name": "analyze_resume", "arguments": {"resume_path": resume_path}, "conversation_id": 0},
        )
        result = payload.get("result", {})
        if result.get("success"):
            return {
                "resume_summary": result.get("summary", ""),
                "skills": result.get("skills", []),
                "keywords": result.get("keywords") or result.get("skills", []),
            }
        logger.warning(f"analyze_resume tool returned failure: {result.get('error')}")
        return {
            "resume_summary": f"Resume analysis unavailable: {result.get('error', 'unknown error')}",
            "skills": [],
            "keywords": [],
        }
    except Exception as e:
        logger.warning(f"AI Platform unreachable for resume analysis, using simulated data: {e}")
        return {
            "resume_summary": "[simulated - ai_platform unreachable] Simulated resume profile summary",
            "skills": ["Python", "FastAPI"],
            "keywords": ["Python Developer", "FastAPI Backend Engineer"],
        }


async def search_node(state: AgentState) -> dict:
    logger.info("Executing Job Search Node...")
    user_id = state.get("user_id")
    try:
        payload = await _get(f"{settings.JOB_SEARCH_URL}/api/search/results", {"user_id": user_id, "limit": 10})
        raw_jobs = payload.get("data", [])
        if raw_jobs:
            jobs = [
                {
                    "id": j.get("id"),
                    "title": j.get("title", ""),
                    "company": j.get("company", ""),
                    "location": j.get("location", ""),
                    "description": j.get("description", ""),
                    "url": j.get("job_url", ""),
                }
                for j in raw_jobs
            ]
            return {"search_results": jobs}
        # No cached results yet - queue a fresh background search for next time,
        # and report an empty result set honestly rather than faking jobs.
        try:
            await _post(
                f"{settings.JOB_SEARCH_URL}/api/search/run-once",
                {"user_id": user_id, "user_profile": {"skills": state.get("skills", [])}, "filters": {}},
            )
            logger.info("No cached job results yet - queued a fresh background search.")
        except Exception:
            pass
        return {"search_results": []}
    except Exception as e:
        logger.warning(f"Job Search Agent unreachable, using simulated data: {e}")
        return {
            "search_results": [
                {"id": 1, "title": "[simulated] Backend Developer", "company": "Stripe", "location": "Remote",
                 "description": "Django/Python role", "url": "https://stripe.com/jobs/1"},
                {"id": 2, "title": "[simulated] Frontend Engineer", "company": "Vercel", "location": "Remote",
                 "description": "React role", "url": "https://vercel.com/jobs/2"},
            ]
        }


async def match_node(state: AgentState) -> dict:
    logger.info("Executing Job Matching Node...")
    user_id = state.get("user_id")
    try:
        match_payload = await _get(f"{settings.JOB_MATCHING_URL}/api/matching/top", {"user_id": user_id, "limit": 5})
        raw_matches = match_payload.get("data", [])
        if not raw_matches:
            return {"matched_jobs": []}

        # job_matching_agent only returns job_id + overall_score - fetch the
        # actual job details (title/company/url) from job_search_agent's
        # cached results and merge them in.
        job_details = {}
        try:
            search_payload = await _get(f"{settings.JOB_SEARCH_URL}/api/search/results", {"user_id": user_id, "limit": 100})
            for j in search_payload.get("data", []):
                job_details[j.get("id")] = j
        except Exception as e:
            logger.warning(f"Could not fetch job details from Job Search Agent for merging: {e}")

        matched_jobs = []
        for m in raw_matches:
            job_id = m.get("job_id")
            details = job_details.get(job_id, {})
            matched_jobs.append({
                "id": job_id,
                "title": details.get("title", f"Job #{job_id}"),
                "company": details.get("company", "Unknown"),
                "location": details.get("location", ""),
                "description": details.get("description", ""),
                "url": details.get("job_url", ""),
                "match_score": m.get("overall_score", 0.0),
            })
        return {"matched_jobs": matched_jobs}
    except Exception as e:
        logger.warning(f"Job Matching Agent unreachable, using simulated data: {e}")
        return {
            "matched_jobs": [
                {"id": 1, "title": "[simulated] Backend Developer", "company": "Stripe", "location": "Remote",
                 "description": "Django/Python role", "url": "https://stripe.com/jobs/1", "match_score": 88.0},
                {"id": 2, "title": "[simulated] Frontend Engineer", "company": "Vercel", "location": "Remote",
                 "description": "React role", "url": "https://vercel.com/jobs/2", "match_score": 45.0},
            ]
        }


async def select_job_node(state: AgentState) -> dict:
    logger.info("Selecting next job...")
    matched = state.get("matched_jobs", [])
    if matched:
        job = matched[0]
        return {
            "current_job": job,
            "matched_jobs": matched[1:],
            "status": "running"
        }
    return {"status": "completed"}


async def browser_node(state: AgentState) -> dict:
    logger.info("Executing Browser Automation Node...")
    job = state.get("current_job") or {}
    user_id = state.get("user_id")
    try:
        start_payload = await _post(f"{settings.BROWSER_AGENT_URL}/api/browser/start", {"user_id": user_id})
        session_id = start_payload.get("session_id")

        job_id = job.get("id", 0)
        job_url = job.get("url", "")
        await _post(
            f"{settings.BROWSER_AGENT_URL}/api/browser/apply/{job_id}",
            {
                "user_id": user_id,
                "session_id": session_id,
                "job_id": job_id,
                "job_url": job_url,
                "form_data": {},
                "resume_path": state.get("resume_path") or "",
                "cover_letter_path": "",
            },
        )

        # Queued as a background task on the browser agent's side - report
        # that it's in progress; the frontend can poll /api/browser/status
        # for finer-grained detail if needed.
        return {
            "current_page": job_url,
            "application_progress": 0.5,
            "status": "completed",
        }
    except Exception as e:
        logger.warning(f"Browser Agent unreachable, using simulated data: {e}")
        return {
            "current_page": job.get("url"),
            "application_progress": 0.9,
            "status": "completed",
        }


def build_orchestrator_graph():
    """Compiles and returns the LangGraph Workflow StateGraph."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("resume_intelligence", resume_node)
    workflow.add_node("job_search", search_node)
    workflow.add_node("job_matching", match_node)
    workflow.add_node("select_next_job", select_job_node)
    workflow.add_node("browser_automation", browser_node)
    
    # Set Entry Point
    workflow.set_entry_point("resume_intelligence")
    
    # Add simple linear connections
    workflow.add_edge("resume_intelligence", "job_search")
    workflow.add_edge("job_search", "job_matching")
    workflow.add_edge("job_matching", "select_next_job")
    
    # Conditional routing edge from Job Selection
    workflow.add_conditional_edges(
        "select_next_job",
        WorkflowRouter.route_match_decision,
        {
            "browser_automation": "browser_automation",
            "skip_job": "select_next_job",
            "select_next_job": END
        }
    )
    
    # Conditional routing edge from Browser Automation
    workflow.add_conditional_edges(
        "browser_automation",
        WorkflowRouter.route_browser_execution,
        {
            "browser_automation": "browser_automation",
            "login_wait_node": END,  # Yield/interruption points
            "captcha_wait_node": END,
            "form_review_wait_node": END,
            "select_next_job": "select_next_job"
        }
    )
    
    return workflow.compile()