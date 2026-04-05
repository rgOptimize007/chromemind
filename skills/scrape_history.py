import os
import sqlite3
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from chromemind.errors import SkillError, ChromeNotFoundError

def scrape_history(profile_name: str, limit: int, history_days: int) -> list[dict]:
    """Reads Chrome History SQLite DB."""
    appdata = os.environ.get("LOCALAPPDATA")
    if not appdata:
        raise SkillError("LOCALAPPDATA environment variable not found")
        
    db_path = os.path.join(appdata, "Google", "Chrome", "User Data", profile_name, "History")
    if not os.path.exists(db_path):
        raise ChromeNotFoundError(f"History file not found at {db_path}")
        
    # Copy DB to temp file because Chrome locks it
    fd, temp_db = tempfile.mkstemp()
    os.close(fd)
    try:
        shutil.copy2(db_path, temp_db)
    except Exception as e:
        os.remove(temp_db)
        raise SkillError(f"Failed to copy History DB: {e}")

    results = []
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Chrome uses microseconds since 1601-01-01 UTC
        earliest_time_unix = (datetime.now(timezone.utc) - timedelta(days=history_days)).timestamp()
        chrome_epoch_diff = 11644473600  
        earliest_time_webkit = int((earliest_time_unix + chrome_epoch_diff) * 1_000_000)

        query = f"""
            SELECT url, title, visit_count, last_visit_time 
            FROM urls 
            WHERE last_visit_time >= {earliest_time_webkit}
            ORDER BY last_visit_time DESC 
        """
        cursor.execute(query)
        
        for row in cursor.fetchall():
            url, title, visit_count, last_visit_time = row
            if url.startswith("chrome://") or url.startswith("chrome-extension://"):
                continue
                
            unix_time = (last_visit_time / 1_000_000) - chrome_epoch_diff
            iso_time = datetime.fromtimestamp(unix_time, timezone.utc).isoformat()
            
            results.append({
                "url": url,
                "title": title,
                "visit_count": visit_count,
                "last_visited_at": iso_time
            })
            if len(results) >= limit:
                break
    except Exception as e:
        raise SkillError(f"History DB query failed: {e}")
    finally:
        conn.close()
        os.remove(temp_db)
        
    return results[:limit]
