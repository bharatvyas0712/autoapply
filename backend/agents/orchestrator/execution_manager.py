from typing import Dict, Any, Optional
from graph import build_orchestrator_graph
from checkpoint import StateCheckpointer
from repository import AsyncSessionLocal, OrchestratorSession
from sqlalchemy.future import select
from utilities.logger import get_logger

logger = get_logger("ExecutionManager")

# Holds current in-memory status of workflows: session_id -> state
_active_workflows: Dict[int, Dict[str, Any]] = {}

class ExecutionManager:
    """
    Spawns, stops, pauses, and resumes running instances of the LangGraph workflow.
    """
    
    @staticmethod
    async def get_state(session_id: int) -> Optional[Dict[str, Any]]:
        # Load from active run cache first
        if session_id in _active_workflows:
            return _active_workflows[session_id]
        # Fallback to DB checkpointer
        return await StateCheckpointer.load_checkpoint(session_id)

    @staticmethod
    async def start_workflow(user_id: int, resume_path: str = "") -> int:
        async with AsyncSessionLocal() as db:
            session = OrchestratorSession(user_id=user_id, status="running")
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id
            
        initial_state = {
            "user_id": user_id,
            "session_id": session_id,
            "resume_path": resume_path,
            "resume_text": None,
            "resume_summary": None,
            "skills": [],
            "keywords": [],
            "search_results": [],
            "matched_jobs": [],
            "current_job": None,
            "current_page": None,
            "application_progress": 0.0,
            "generated_answers": {},
            "status": "running",
            "errors": [],
            "logs": ["Workflow initiated."],
            "next_step": "resume_intelligence"
        }
        
        _active_workflows[session_id] = initial_state
        await StateCheckpointer.save_checkpoint(session_id, "init", initial_state)
        
        # Trigger execution in background task / async task
        asyncio.create_task(ExecutionManager._run_graph_loop(session_id))
        return session_id

    @staticmethod
    async def _run_graph_loop(session_id: int):
        compiled_graph = build_orchestrator_graph()
        state = _active_workflows.get(session_id)
        if not state:
            return
            
        logger.info(f"Starting execution loop for session {session_id}")
        
        # Traverse graph nodes manually or compile inputs
        try:
            # We mock the thread step execution for the compiled state graph
            async for event in compiled_graph.astream(state):
                # Update local in-memory trace state
                for node_name, output in event.items():
                    logger.info(f"Node execution complete: {node_name}")
                    state.update(output)
                    state["logs"].append(f"Completed node: {node_name}")
                    await StateCheckpointer.save_checkpoint(session_id, node_name, state)
                    
                    # Log execution history (Mocked runtimes)
                    from history import HistoryLogger
                    await HistoryLogger.log_node_execution(session_id, node_name, 1.2, "success", None, output)
                    
                # Pause logic evaluation
                if state.get("status", "running").startswith("paused"):
                    logger.info(f"Session {session_id} entered paused state: {state['status']}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in graph execution loop: {e}")
            state["status"] = "failed"
            state["errors"].append(str(e))
            await StateCheckpointer.save_checkpoint(session_id, "error", state)

    @staticmethod
    async def pause_workflow(session_id: int, reason: str = "manual"):
        state = _active_workflows.get(session_id)
        if state:
            state["status"] = f"paused_{reason}"
            state["logs"].append(f"Workflow paused. Reason: {reason}")
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
                sess = result.scalars().first()
                if sess:
                    sess.status = f"paused_{reason}"
                    await db.commit()
            return True
        return False

    @staticmethod
    async def resume_workflow(session_id: int):
        state = _active_workflows.get(session_id)
        if state:
            state["status"] = "running"
            state["logs"].append("Workflow resumed by user.")
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
                sess = result.scalars().first()
                if sess:
                    sess.status = "running"
                    await db.commit()
            
            # Restart graph loop execution
            asyncio.create_task(ExecutionManager._run_graph_loop(session_id))
            return True
        return False

    @staticmethod
    async def stop_workflow(session_id: int):
        state = _active_workflows.pop(session_id, None)
        if state:
            state["status"] = "stopped"
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
                sess = result.scalars().first()
                if sess:
                    sess.status = "stopped"
                    import datetime
                    sess.completed_at = datetime.datetime.utcnow()
                    await db.commit()
            return True
        return False

import asyncio