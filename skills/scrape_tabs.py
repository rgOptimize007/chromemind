import urllib.request
import json
from chromemind.errors import SkillError

def scrape_tabs(remote_debug_port: int, limit: int) -> list[dict]:
    """Retrieves active tabs via Chrome DevTools Protocol."""
    url = f"http://localhost:{remote_debug_port}/json"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        raise SkillError(f"Failed to connect to Chrome DevTools at {url}. Make sure Chrome is started with --remote-debugging-port={remote_debug_port}. Error: {e}")
        
    results = []
    for tab in data:
        if tab.get("type") == "page":
            tab_url = tab.get("url", "")
            if tab_url.startswith("chrome://") or tab_url.startswith("chrome-extension://"):
                continue
            
            results.append({
                "url": tab_url,
                "title": tab.get("title", ""),
                "tab_group_name": None 
            })
            if len(results) >= limit:
                break
                
    return results[:limit]
