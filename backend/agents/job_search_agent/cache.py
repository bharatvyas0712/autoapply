from typing import Any

class JobCache:
    """
    Simple in-memory async cache for job search duplicate prevention across sessions.
    In a fully distributed environment, this would be backed by Redis.
    """
    def __init__(self):
        self._cache = set()
        
    async def add_job(self, job_hash: str):
        self._cache.add(job_hash)
        
    async def is_processed(self, job_hash: str) -> bool:
        return job_hash in self._cache
        
    async def clear(self):
        self._cache.clear()

# Global cache instance
job_cache = JobCache()
