from repository import AsyncSessionLocal, OrchestratorSession
from sqlalchemy.future import select
from utilities.logger import get_logger

logger = get_logger("ApprovalManager")

class ApprovalManager:
    """
    Evaluates human approval state for low-confidence answers and CAPTCHAs.
    """
    
    @staticmethod
    async def request_approval(session_id: int, element_type: str, item_id: int):
        logger.info(f"Session {session_id} requesting human approval for {element_type} ID {item_id}")
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
            sess = result.scalars().first()
            if sess:
                sess.status = f"paused_{element_type}"
                await db.commit()
                
    @staticmethod
    async def resume_session(session_id: int):
        logger.info(f"Session {session_id} resuming following human resolution.")
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
            sess = result.scalars().first()
            if sess:
                sess.status = "running"
                await db.commit()
                return True
        return False
