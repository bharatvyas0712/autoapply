from memory_store import MemoryStore
from typing import Dict, Any

class EpisodicMemory:
    """Manages episodic application process logs."""
    @staticmethod
    async def record_episode(user_id: int, job_id: int, steps: list):
        await MemoryStore.store_memory(
            user_id=user_id,
            memory_type="episodic",
            key=f"execution_run_job_{job_id}",
            value={"job_id": job_id, "steps": steps}
        )
