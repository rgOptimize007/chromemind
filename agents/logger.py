from chromemind.schemas import RunConfigLogging
from skills.format_log_entry import format_log_entry
from skills.write_log import write_log
from chromemind.guardrails import check_api_key_not_in_log
import logging

class LoggerAgent:
    @staticmethod
    def log(agent: str, event: str, level: str, payload: dict | None = None, config: RunConfigLogging | None = None):
        """Cross-cutting logger agent."""
        if config:
            levels = ["debug", "info", "warn", "error"]
            try:
                if levels.index(level) < levels.index(config.level):
                    return
            except ValueError:
                pass
                
        # Guardrail check
        safe_event = check_api_key_not_in_log(event)
        
        entry = format_log_entry(agent, safe_event, level, payload)
        
        # Log to stdout for CLI feedback
        if level == "error":
            logging.error(f"[{agent}] {safe_event}")
        else:
            logging.info(f"[{agent}] {safe_event}")
            
        write_log(entry, retain_days=config.retain_days if config else 7)
