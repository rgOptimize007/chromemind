from chromemind.schemas import RawItem, EnrichedItem


def map_to_notion_schema(item: RawItem | EnrichedItem) -> dict:
    """Maps a RawItem or EnrichedItem into Notion page properties dict."""
    props = {
        "Name": {"title": [{"text": {"content": item.title}}]},
        "URL": {"url": item.url},
        "Source": {"select": {"name": item.source}},
        "Timestamp": {"date": {"start": item.scraped_at}},
        "ChromeMind ID": {"rich_text": [{"text": {"content": item.id}}]},
        "Status": {"select": {"name": "Unread"}},
    }

    if item.folder_path:
        props["Folder Path"] = {"rich_text": [{"text": {"content": item.folder_path}}]}

    if item.visit_count is not None:
        props["Visit Count"] = {"number": item.visit_count}

    # Enrichment fields (only present on EnrichedItem)
    if isinstance(item, EnrichedItem) and item.enriched_at:
        if item.category:
            props["Category"] = {"select": {"name": item.category}}

        if item.tags:
            props["Tags"] = {"multi_select": [{"name": t} for t in item.tags]}

        if item.summary:
            props["Summary"] = {"rich_text": [{"text": {"content": item.summary}}]}

        if item.priority_score is not None:
            props["Priority Score"] = {"number": item.priority_score}

        if item.priority_reason:
            props["Priority Reason"] = {"rich_text": [{"text": {"content": item.priority_reason}}]}

        if item.read_time:
            props["Read Time"] = {"rich_text": [{"text": {"content": item.read_time}}]}

        if item.enriched_at:
            props["Enriched At"] = {"date": {"start": item.enriched_at}}

        props["Needs Review"] = {"checkbox": item.needs_review}

    return props
