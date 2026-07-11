import asyncio
from typing import Callable, Any
from utilities.logger import get_logger

logger = get_logger("RetryManager")

class RetryManager:
    """
    Wraps asynchronous microservice execution runs with retry counts and backoff.
    """
    
    @staticmethod
    async def execute_with_retry(func: Callable, max_attempts: int = 3, delay: float = 1.0, *args, **kwargs) -> Any:
        attempt = 0
        current_delay = delay
        
        while attempt < max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                logger.warning(f"Execution failed on attempt {attempt}/{max_attempts}: {e}")
                if attempt == max_attempts:
                    logger.error(f"Execution failed after maximum retries.")
                    raise e
                await asyncio.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
