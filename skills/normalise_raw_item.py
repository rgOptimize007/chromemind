import hashlib
from datetime import datetime, timezone
from chromemind.schemas import RawItem

def normalise_raw_item(raw: dict, source: str) -> RawItem:
    """
    Normalises varying input structures into a unified RawItem.
    Expects raw to have: url, title. Optional: folder_path, tab_group_name, visit_count, last_visited_at
    """
    url = raw.get("url", "")
    if not url:
        raise ValueError("Cannot normalise item without a URL")
        
    id_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    
    # Allow passing through pre-formatted timestamps (e.g., from scraping)
    scraped_at = raw.get("scraped_at") or raw.get("last_visited_at") or datetime.now(timezone.utc).isoformat()
    visit_count = raw.get("visit_count", None)
    if source == "history" and visit_count is None:
        visit_count = 1
        
    return RawItem(
        id=id_hash,
        url=url,
        title=raw.get("title", ""),
        source=source,
        folder_path=raw.get("folder_path"),
        scraped_at=scraped_at,
        visit_count=visit_count,
        tab_group_name=raw.get("tab_group_name")
    )
