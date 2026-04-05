import json
from datetime import datetime, timezone
from typing import Any

def format_log_entry(agent: str, event: str, level: str, payload: dict | None = None) -> str:
    """Formats a structured log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "agent": agent,
        "event": event
    }
    if payload:
        entry["payload"] = payload
    return json.dumps(entry)
