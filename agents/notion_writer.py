import asyncio
from chromemind.schemas import RunConfig, RawItem, WriteReport
from skills.notion_upsert import notion_upsert
from agents.logger import LoggerAgent

class NotionWriterAgent:
    @staticmethod
    async def run(items: list[RawItem], config: RunConfig) -> WriteReport:
        LoggerAgent.log("notion_writer", "started", "info", {"item_count": len(items)}, config.logging)
        report = WriteReport()
        
        for idx, item in enumerate(items):
            res = notion_upsert(item, config.notion)
            status = res.get("status")
            
            if status == "created":
                report.created += 1
            elif status == "updated":
                report.updated += 1
            elif status in ("skipped_duplicate", "skipped_dry_run", "skipped"):
                report.skipped += 1
            else:
                report.failed.append({"id": item.id, "reason": res.get("reason", "Unknown")})
                
            LoggerAgent.log("notion_writer", f"item_processed", "debug", 
                            {"id": item.id, "status": status}, config.logging)
            
            if idx < len(items) - 1:
                await asyncio.sleep(0.34)
                
        LoggerAgent.log("notion_writer", "finished", "info", report.model_dump(), config.logging)
        return report
