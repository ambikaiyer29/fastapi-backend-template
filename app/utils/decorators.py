# app/utils/decorators.py
import inspect  # <-- IMPORT THE INSPECT MODULE
from functools import wraps
from time import time
from app.core.logging import get_logger

logger = get_logger(__name__)


def log_request(func):
    """
    Decorator to log incoming requests, processing time, and results.
    This decorator is "universal" and works with both `def` and `async def` functions.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time()
        logger.info(f"Request started for endpoint: {func.__name__}")

        # --- THIS IS THE FIX ---
        # Check if the wrapped function is a coroutine (async def) or a regular function (def)
        if inspect.iscoroutinefunction(func):
            # If it's async, await it
            response = await func(*args, **kwargs)
        else:
            # If it's sync, just call it
            response = func(*args, **kwargs)
        # --- END OF FIX ---

        process_time = time() - start_time
        logger.info(
            f"Request to endpoint {func.__name__} finished in {process_time:.4f} seconds"
        )
        return response

    return wrapper