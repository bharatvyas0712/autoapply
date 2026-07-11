import asyncio
from functools import wraps
from utilities.logger import get_logger

logger = get_logger("retry")

def async_retry(max_retries=3, base_delay=1.0):
    """
    Exponential backoff retry decorator for async functions.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    logger.warning(f"Function {func.__name__} failed on attempt {attempt+1}. Retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
        return wrapper
    return decorator
