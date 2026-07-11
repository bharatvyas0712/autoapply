"""
Retry utilities with exponential backoff for resilient automation.
"""

import time
import random
from functools import wraps
from typing import Callable, Optional, Type, Tuple
from logger_config import logger


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to avoid thundering herd
        retryable_exceptions: Tuple of exception types to retry on
        on_retry: Optional callback function called on each retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise RetryError(f"Failed after {max_attempts} attempts") from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call on_retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, delay)
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def retry_operation(
    operation: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    operation_name: str = "operation"
) -> any:
    """
    Retry an operation with exponential backoff (non-decorator version).
    
    Args:
        operation: Callable to retry
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        operation_name: Name of the operation for logging
    
    Returns:
        Result of the operation if successful
    
    Raises:
        RetryError: If all attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as e:
            last_exception = e
            
            if attempt == max_attempts - 1:
                logger.error(f"All {max_attempts} attempts failed for {operation_name}")
                raise RetryError(f"Failed after {max_attempts} attempts") from e
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            delay = delay * (0.5 + random.random() * 0.5)  # Add jitter
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_attempts} failed for {operation_name}: {str(e)}. "
                f"Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
    
    raise last_exception
