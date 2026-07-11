from repository import AsyncSessionLocal, NodeExecutionHistory
from typing import Dict, Any, List
from sqlalchemy.future import select
from sqlalchemy import desc

class HistoryLogger:
    """
    Saves trace outputs and runtimes of orchestrator nodes to MySQL.
    """
    
    @staticmethod
    async def log_node_execution(session_id: int, node_name: str, duration: float, status: str, error: str = None, output: dict = None):
        async with AsyncSessionLocal() as db:
            log = NodeExecutionHistory(
                session_id=session_id,
                node_name=node_name,
                execution_time_sec=duration,
                status=status,
                error_message=error,
                agent_output=output
            )
            db.add(log)
            await db.commit()

    @staticmethod
    async def get_execution_history(session_id: int) -> List[NodeExecutionHistory]:
        async with AsyncSessionLocal() as db:
            stmt = select(NodeExecutionHistory).where(NodeExecutionHistory.session_id == session_id).order_by(desc(NodeExecutionHistory.created_at))
            result = await db.execute(stmt)
            return [r.to_dict() for r in result.scalars().all()]
