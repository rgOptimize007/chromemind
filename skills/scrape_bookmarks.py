import os
import json
from chromemind.errors import SkillError, ChromeNotFoundError

def scrape_bookmarks(profile_name: str, limit: int) -> list[dict]:
    """Reads Chrome local Bookmarks JSON, parses recursively."""
    appdata = os.environ.get("LOCALAPPDATA")
    if not appdata:
        raise SkillError("LOCALAPPDATA environment variable not found")
        
    path = os.path.join(appdata, "Google", "Chrome", "User Data", profile_name, "Bookmarks")
    if not os.path.exists(path):
        raise ChromeNotFoundError(f"Bookmarks file not found at {path}")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise SkillError(f"Failed to read Bookmarks file: {e}")
        
    results = []
    
    def traverse(node, current_path):
        if len(results) >= limit:
            return
            
        if node.get("type") == "url":
            results.append({
                "url": node.get("url"),
                "title": node.get("name"),
                "folder_path": current_path
            })
        elif node.get("type") == "folder":
            new_path = f"{current_path} > {node.get('name')}" if current_path else node.get("name")
            for child in node.get("children", []):
                traverse(child, new_path)
                
    roots = data.get("roots", {})
    for key in ["bookmark_bar", "other", "synced"]:
        if root_node := roots.get(key):
            traverse(root_node, "")
            
    return results[:limit]
