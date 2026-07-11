from repository import AsyncSessionLocal, OrchestratorMemory
from sqlalchemy.future import select
from typing import Dict, Any, Optional

class OrchestratorMemoryManager:
    """
    Manages key-value memory blocks (conversation, resume context, company details) in DB.
    """
    
    @staticmethod
    async def get_memory(user_id: int, key: str) -> Optional[Dict[str, Any]]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OrchestratorMemory).where(
                    OrchestratorMemory.user_id == user_id,
                    OrchestratorMemory.memory_key == key
                )
            )
            mem = result.scalars().first()
            return mem.memory_value if mem else None

    @staticmethod
    async def save_memory(user_id: int, key: str, value: Dict[str, Any]):
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OrchestratorMemory).where(
                    OrchestratorMemory.user_id == user_id,
                    OrchestratorMemory.memory_key == key
                )
            )
            mem = result.scalars().first()
            if mem:
                mem.memory_value = value
            else:
                mem = OrchestratorMemory(user_id=user_id, memory_key=key, memory_value=value)
                db.add(mem)
            await db.commit()
