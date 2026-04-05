import logging
from typing import Any, Callable
from notion_client import APIResponseError
import time

logger = logging.getLogger(__name__)

def handle_notion_errors(func: Callable) -> Callable:
    """Wraps a Notion Client call with basic retry logic on rate/server errors."""
    def wrapper(*args, **kwargs) -> dict[str, Any]:
        retries = 1
        for attempt in range(retries + 1):
            try:
                return {"status": "success", "result": func(*args, **kwargs)}
            except APIResponseError as e:
                # 429 Too Many Requests, 502/503/504 Server Errors
                if getattr(e, 'status', 500) in (429, 502, 503, 504) and attempt < retries:
                    logger.warning(f"Notion API error {getattr(e, 'status', 500)}. Retrying...")
                    time.sleep(1)
                    continue
                return {"status": "failed", "reason": str(e)}
            except Exception as e:
                return {"status": "failed", "reason": str(e)}
        return {"status": "failed", "reason": "Max retries exceeded"}
    return wrapper
