import os
from notion_client import Client
from chromemind.schemas import RawItem, RunConfigNotion
from .map_to_notion_schema import map_to_notion_schema
from .handle_notion_errors import handle_notion_errors
from chromemind.guardrails import check_before_write

@handle_notion_errors
def _notion_query(client: Client, database_id: str, id_hash: str):
    return client.databases.query(
        database_id=database_id,
        filter={
            "property": "ChromeMind ID",
            "rich_text": {"equals": id_hash}
        }
    )

@handle_notion_errors
def _notion_create(client: Client, database_id: str, properties: dict):
    return client.pages.create(
        parent={"database_id": database_id},
        properties=properties
    )

@handle_notion_errors
def _notion_update(client: Client, page_id: str, properties: dict):
    return client.pages.update(
        page_id=page_id,
        properties=properties
    )

def notion_upsert(item: RawItem, config: RunConfigNotion) -> dict:
    """Upserts item to Notion database."""
    # Check guardrails (dry_run check)
    from types import SimpleNamespace
    check_config = SimpleNamespace(notion=config)
    
    try:
        check_before_write(item.model_dump(), check_config)
    except Exception as e:
        return {"status": "skipped_dry_run", "reason": str(e)}

    token = os.environ.get("NOTION_TOKEN")
    if not token:
        return {"status": "failed", "reason": "NOTION_TOKEN not set in environment."}
        
    client = Client(auth=token)
    
    # 1. Check if exists
    query_resp = _notion_query(client, config.database_id, item.id)
    if query_resp["status"] == "failed":
        return query_resp
        
    results = query_resp["result"].get("results", [])
    properties = map_to_notion_schema(item)
    
    if results:
        # Page exists
        if config.duplicate_strategy == "skip":
            return {"status": "skipped_duplicate", "reason": "duplicate_strategy is skip"}
            
        page = results[0]
        
        # Remove protected fields
        for field in config.protected_fields:
            if field in properties:
                del properties[field]
                
        # Update
        res = _notion_update(client, page["id"], properties)
        if res["status"] == "success":
            return {"status": "updated", "result": res["result"]}
        return res
    else:
        # Create
        res = _notion_create(client, config.database_id, properties)
        if res["status"] == "success":
            return {"status": "created", "result": res["result"]}
        return res
