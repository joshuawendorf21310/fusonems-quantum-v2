"""
Retry utility for external API calls with exponential backoff.
"""
import asyncio
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[tuple] = None,
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: Tuple of exception types to retry on (default: all exceptions)
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    """
    if retry_on is None:
        retry_on = (Exception,)
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except retry_on as e:
            last_exception = e
            
            if attempt < max_retries:
                # Calculate delay with exponential backoff
                delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s: {type(e).__name__}: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} retry attempts failed: {type(e).__name__}: {e}")
                raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry_sync(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[tuple] = None,
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    Args:
        func: Synchronous function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on: Tuple of exception types to retry on (default: all exceptions)
    
    Returns:
        Result of the function call
    
    Raises:
        Last exception if all retries fail
    """
    import time
    
    if retry_on is None:
        retry_on = (Exception,)
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except retry_on as e:
            last_exception = e
            
            if attempt < max_retries:
                # Calculate delay with exponential backoff
                delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s: {type(e).__name__}: {e}"
                )
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} retry attempts failed: {type(e).__name__}: {e}")
                raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry_decorator(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retry_on: Optional[tuple] = None,
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Usage:
        @retry_decorator(max_retries=3)
        async def my_api_call():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _call():
                return await func(*args, **kwargs)
            return await retry_with_backoff(
                _call,
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                retry_on=retry_on,
            )
        return wrapper
    return decorator
