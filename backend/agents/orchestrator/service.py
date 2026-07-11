from execution_manager import ExecutionManager
from history import HistoryLogger
from workflow_builder import WorkflowBuilder
from repository import AsyncSessionLocal, OrchestratorSession
from sqlalchemy.future import select
from typing import Dict, Any, List

class OrchestratorService:
    @staticmethod
    async def start_workflow(user_id: int, resume_path: str = "") -> int:
        return await ExecutionManager.start_workflow(user_id, resume_path)

    @staticmethod
    async def pause_workflow(session_id: int, reason: str = "manual") -> bool:
        return await ExecutionManager.pause_workflow(session_id, reason)

    @staticmethod
    async def resume_workflow(session_id: int) -> bool:
        return await ExecutionManager.resume_workflow(session_id)

    @staticmethod
    async def stop_workflow(session_id: int) -> bool:
        return await ExecutionManager.stop_workflow(session_id)

    @staticmethod
    async def get_state(session_id: int) -> Dict[str, Any]:
        state = await ExecutionManager.get_state(session_id)
        return {"success": True, "state": state}

    @staticmethod
    async def get_history(session_id: int) -> List[Any]:
        return await HistoryLogger.get_execution_history(session_id)

    @staticmethod
    def get_mermaid_graph() -> str:
        return WorkflowBuilder.generate_mermaid()

    @staticmethod
    def get_png_graph() -> bytes:
        return WorkflowBuilder.generate_png()
        
    @staticmethod
    async def get_sessions(user_id: int) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.user_id == user_id))
            return [s.to_dict() for s in result.scalars().all()]
