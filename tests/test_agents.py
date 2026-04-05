from unittest.mock import patch, MagicMock
from agents.scraper import ScraperAgent
from chromemind.schemas import RunConfig
import pytest

@patch("agents.scraper.scrape_bookmarks")
@patch("agents.scraper.scrape_history")
@patch("agents.scraper.scrape_tabs")
def test_scraper_agent_run(mock_scrape_tabs, mock_scrape_history, mock_scrape_bookmarks, mock_config):
    # Setup mocks
    mock_scrape_bookmarks.return_value = [{"url": "https://bm.com", "title": "BM"}]
    mock_scrape_history.return_value = [{"url": "https://hist.com", "title": "Hist"}]
    mock_scrape_tabs.return_value = [{"url": "https://tab.com", "title": "Tab"}]

    results = ScraperAgent.run(mock_config)

    assert len(results) == 3
    sources = set(r.source for r in results)
    assert sources == {"bookmark", "history", "tab"}
    
def test_scraper_agent_deduplication(mock_config):
    with patch("agents.scraper.scrape_tabs") as mock_scrape_tabs:
        # Override to only run tabs
        mock_scrape_tabs.return_value = [
            {"url": "https://dup.com", "title": "Dup 1"},
            {"url": "https://dup.com", "title": "Dup 2"},
        ]
        results = ScraperAgent.run(mock_config, override_source="tabs")
        
        # Should deduplicate based on URL (id hash)
        assert len(results) == 1
        assert results[0].url == "https://dup.com"
