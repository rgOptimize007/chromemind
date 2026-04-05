from chromemind.schemas import RunConfig, RawItem
from skills.scrape_bookmarks import scrape_bookmarks
from skills.scrape_history import scrape_history
from skills.scrape_tabs import scrape_tabs
from skills.normalise_raw_item import normalise_raw_item
from agents.logger import LoggerAgent

class ScraperAgent:
    @staticmethod
    def run(config: RunConfig, override_source: str | None = None, override_limit: int | None = None) -> list[RawItem]:
        LoggerAgent.log("scraper", "started", "info", {"override_source": override_source}, config.logging)
        
        raw_items = []
        limit = override_limit or config.limits.max_items_per_source
        
        sources_to_run = []
        if override_source == "all" or not override_source:
             if config.sources.bookmarks: sources_to_run.append("bookmarks")
             if config.sources.history: sources_to_run.append("history")
             if config.sources.tab_groups: sources_to_run.append("tabs")
        else:
             sources_to_run.append(override_source)
             
        for source in sources_to_run:
            LoggerAgent.log("scraper", f"scraping_{source}", "debug", config=config.logging)
            try:
                if source == "bookmarks":
                    results = scrape_bookmarks(config.chrome.profile, limit)
                elif source == "history":
                    results = scrape_history(config.chrome.profile, limit, config.chrome.history_days)
                elif source == "tabs":
                    results = scrape_tabs(config.chrome.remote_debug_port, limit)
                else:
                    results = []
                    
                for r in results:
                    schema_source = source[:-1] if source.endswith('s') else source
                    raw_items.append(normalise_raw_item(r, schema_source))
                    
                LoggerAgent.log("scraper", f"scraped_{source}", "info", {"count": len(results)}, config.logging)
            except Exception as e:
                LoggerAgent.log("scraper", f"error_scraping_{source}", "error", {"error": str(e)}, config.logging)
                
        # Deduplicate
        seen = set()
        deduped = []
        for item in raw_items:
            if item.id not in seen:
                seen.add(item.id)
                deduped.append(item)
                
        LoggerAgent.log("scraper", "finished", "info", {"total_raw": len(raw_items), "total_deduped": len(deduped)}, config.logging)
        return deduped
