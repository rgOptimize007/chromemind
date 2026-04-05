# Phase 3 Walkthrough: Tests, GitAgent, and Tab Groups

This walkthrough details the changes made to the `browser_manager` pipeline to introduce test-driven practices, automate code updates, and correctly extract Chrome Tab Groups.

## 1. Test-Driven Development integration

We introduced `pytest` and a comprehensive fixture framework (`tests/conftest.py`) to systematically validate agent pipelines and skill sub-routines.

**Key Changes:**
- `tests/test_agents.py` now guarantees the deduplication and overriding source logic in `ScraperAgent`.
- `tests/test_skills.py` ensures the `normalise_raw_item` logic constructs accurate SHA256 IDs, even handling legacy history dumps missing formal `visit_count` metadata.
- With these additions, executing `pytest -v` accurately measures core state stability.

## 2. Agentic Git Automation

We established a new, highly privileged `GitAgent` inside `agents/git_agent.py` alongside integrations within the `OrchestratorAgent`.

**Key Behaviours:**
1. **Delegation:** The `OrchestratorAgent` now accepts an `auto_commit` flag. When asserted, it commands the `GitAgent` to initialize a feature branch (`auto-update`).
2. **Squashing:** If the `GitAgent` detects more than 3 local commits against the main branch prior to publishing, it performs a soft reset (`git reset --soft HEAD~N`) condensing the changes into a singular, clean commit history.
3. **PR Conflicts:** Integrating with the local GitHub configuration (`gh` / GitHub MCP), it surfaces PR conflicts programmatically back to the logging ecosystem, halting destructive pushes.

```python
# From orchestrator.py
GitAgent.checkout_feature_branch(feature_branch)
msg = f"chore(state): pipeline update with {len(items_to_write)} items synced"
GitAgent.commit_changes(msg)
GitAgent.push_and_squash_if_needed(feature_branch, threshold=3)
```

## 3. Tab Groups Chrome Extension

Since standard Chrome DevTools endpoints omit mapping for `groupId` attributes, we opted to build a native Manifest V3 Chrome Extension.

**How it works:**
- The extension resides in the `extension/` directory. 
- It holds `tabs` and `tabGroups` permissions, routinely querying them via its background service worker (`background.js`).
- The Python utility `skills/scrape_tabs.py` was fundamentally redesigned. Instead of fetching CDP contexts, it spawns a temporary, localized HTTP listener loop (`http://localhost:9223/submit_tabs`) that intercepts the Tab Groups JSON payload posted directly from the Chrome Extension. 

> [!TIP]
> **Action Required:** Make sure to side-load the `extension/` folder into your browser via `chrome://extensions` (Developer Mode enabled) before running the scraper, as the Python script strictly relies on this background synchronization now.
