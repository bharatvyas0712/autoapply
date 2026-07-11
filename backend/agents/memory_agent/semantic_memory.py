from memory_store import MemoryStore
from typing import Dict, Any

class SemanticMemory:
    """Manages general user preferences and fact lists (skills, desired cities, salary)."""
    @staticmethod
    async def save_preference(user_id: int, key: str, value: Any):
        await MemoryStore.store_memory(
            user_id=user_id,
            memory_type="user_pref",
            key=key,
            value={"val": value}
        )
