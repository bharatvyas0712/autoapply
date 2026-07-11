import time
from typing import Optional

# Simple mock in-memory fallback manager mimicking Redis functions
# for locks, cache, and rate-limiting
class RedisManager:
    """
    Handles connections to Redis, providing caching, session storing,
    distributed locking, and rate limiting algorithms.
    """
    _cache = {}
    _locks = {}
    
    @staticmethod
    def set(key: str, value: str, expire_sec: int = 3600):
        RedisManager._cache[key] = {"val": value, "exp": time.time() + expire_sec}

    @staticmethod
    def get(key: str) -> Optional[str]:
        data = RedisManager._cache.get(key)
        if data and data["exp"] > time.time():
            return data["val"]
        return None

    @staticmethod
    def acquire_lock(lock_name: str, expire_sec: int = 10) -> bool:
        now = time.time()
        active_lock = RedisManager._locks.get(lock_name)
        if not active_lock or active_lock < now:
            RedisManager._locks[lock_name] = now + expire_sec
            return True
        return False

    @staticmethod
    def release_lock(lock_name: str):
        RedisManager._locks.pop(lock_name, None)

    @staticmethod
    def is_rate_limited(client_ip: str, limit: int = 60, window_sec: int = 60) -> bool:
        key = f"rate:{client_ip}"
        now = time.time()
        hits = RedisManager._cache.get(key, {"count": 0, "reset": now + window_sec})
        
        if hits["reset"] < now:
            hits = {"count": 1, "reset": now + window_sec}
        else:
            hits["count"] += 1
            
        RedisManager._cache[key] = hits
        return hits["count"] > limit
