import json
import asyncio
from pathlib import Path
from chromemind.schemas import RunConfig, WriteReport
from skills.parse_config import parse_config
from agents.scraper import ScraperAgent
from agents.enricher import EnrichmentAgent
from agents.notion_writer import NotionWriterAgent
from agents.logger import LoggerAgent
from chromemind.guardrails import check_max_items

class OrchestratorAgent:
    @staticmethod
    async def run(source_override: str | None = None, limit_override: int | None = None,
                  dry_run_override: bool | None = None, enrich: bool = True):
        config = parse_config()
        if dry_run_override is not None:
            config.notion.dry_run = dry_run_override

        LoggerAgent.log("orchestrator", "started", "info", config=config.logging)

        # Step 1: Scrape
        raw_items = ScraperAgent.run(config, source_override, limit_override)

        try:
            check_max_items(len(raw_items), config)
        except Exception as e:
            raw_items = raw_items[:config.limits.max_items_per_run]
            LoggerAgent.log("orchestrator", "guardrail_max_items_triggered", "warn", {"msg": str(e)}, config.logging)

        if not raw_items:
            LoggerAgent.log("orchestrator", "no_items_found", "info", config=config.logging)
            return WriteReport()

        # Step 2: Enrich (optional)
        if enrich:
            LoggerAgent.log("orchestrator", "enrichment_started", "info",
                            {"item_count": len(raw_items)}, config.logging)
            items_to_write = EnrichmentAgent.run(raw_items, config)
            LoggerAgent.log("orchestrator", "enrichment_complete", "info",
                            {"enriched_count": len(items_to_write)}, config.logging)
        else:
            items_to_write = raw_items

        # Step 3: Write to Notion
        report = await NotionWriterAgent.run(items_to_write, config)
        OrchestratorAgent._save_state(report)
        LoggerAgent.log("orchestrator", "completed", "info", report.model_dump(), config.logging)
        return report

    @staticmethod
    def _save_state(report: WriteReport):
        state_dir = Path("state")
        state_dir.mkdir(exist_ok=True)
        state = {"last_run": report.model_dump()}
        with open(state_dir / "last_run.json", "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
