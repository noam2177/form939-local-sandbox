import time
import functools
import logging

logger = logging.getLogger(__name__)

def log_execution_time(func):
    """Decorator to log the execution time of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.debug(f"Executed {func.__name__} in {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def log_execution_time_async(func):
    """Decorator to log the execution time of an async function."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.debug(f"Executed {func.__name__} in {end_time - start_time:.4f} seconds")
        return result
    return wrapper
