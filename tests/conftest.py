import pytest
from chromemind.schemas import RunConfig, RawItem, EnrichedItem

@pytest.fixture
def mock_config():
    return RunConfig(
        version="1.0",
        sources={
            "bookmarks": True,
            "reading_list": False,
            "tab_groups": True,
            "history": True
        },
        limits={
            "max_items_per_source": 10,
            "max_items_per_run": 50,
            "batch_size": 10
        },
        enrichment={
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 1000,
            "categories": ["Tech", "News", "Other"]
        },
        notion={
            "database_id": "mock_db_id",
            "duplicate_strategy": "update",
            "protected_fields": ["priority_reason"],
            "dry_run": False
        },
        guardrails={
            "max_high_priority_percent": 30,
            "allowed_domains": ["github.com", "ycombinator.com", "example.com"]
        },
        logging={
            "level": "debug",
            "retain_days": 7
        },
        chrome={
            "profile": "Default",
            "mcp_timeout_ms": 5000,
            "remote_debug_port": 9222,
            "history_days": 1
        }
    )

@pytest.fixture
def mock_raw_item():
    return RawItem(
        id="item_1",
        url="https://example.com",
        title="Example Site",
        source="bookmark",
        scraped_at="2026-04-05T00:00:00Z"
    )

@pytest.fixture
def mock_enriched_item():
    return EnrichedItem(
        id="item_1",
        url="https://example.com",
        title="Example Site",
        source="bookmark",
        scraped_at="2026-04-05T00:00:00Z",
        category="Tech",
        tags=["example"],
        summary="A test summary",
        priority_score=50,
        read_time="2 min",
        enriched_at="2026-04-05T00:01:00Z"
    )
