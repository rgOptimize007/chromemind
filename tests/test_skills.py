import pytest
from skills.normalise_raw_item import normalise_raw_item
import hashlib

def test_normalise_raw_item_success():
    raw_data = {"url": "https://example.com", "title": "Example", "tab_group_name": "Test Group"}
    item = normalise_raw_item(raw_data, "tab")
    
    assert item.url == "https://example.com"
    assert item.title == "Example"
    assert item.source == "tab"
    assert item.tab_group_name == "Test Group"
    assert item.id == hashlib.sha256(b"https://example.com").hexdigest()

def test_normalise_raw_item_no_url():
    raw_data = {"title": "No URL"}
    with pytest.raises(ValueError):
        normalise_raw_item(raw_data, "bookmark")

def test_normalise_raw_item_default_visit_count_history():
    raw_data = {"url": "https://example.com", "title": "Example"}
    item = normalise_raw_item(raw_data, "history")
    assert item.visit_count == 1
