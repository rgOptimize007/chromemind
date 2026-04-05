import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

def write_log(entry: str, retain_days: int = 7) -> None:
    """Appends entry to daily log and rotates old logs."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = logs_dir / f"chromemind_{today}.log"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
        
    # Rotate logs
    now = datetime.now(timezone.utc)
    for path in logs_dir.glob("chromemind_*.log"):
        if path.is_file():
            stat = path.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            if now - mtime > timedelta(days=retain_days):
                path.unlink()
