from repository import AsyncSessionLocal, OrchestratorSession
from sqlalchemy.future import select
from typing import Dict, Any, Optional
import json

class StateCheckpointer:
    """
    Saves and loads state checkpoints to the database to support workflow pausing/resuming.
    """
    
    @staticmethod
    async def save_checkpoint(session_id: int, current_node: str, state: Dict[str, Any]):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
            sess = result.scalars().first()
            if sess:
                sess.current_node = current_node
                sess.checkpoint_state = state
                await db.commit()

    @staticmethod
    async def load_checkpoint(session_id: int) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(OrchestratorSession).where(OrchestratorSession.id == session_id))
            sess = result.scalars().first()
            if sess and sess.checkpoint_state:
                return sess.checkpoint_state
        return None
