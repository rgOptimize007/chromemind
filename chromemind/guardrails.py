import logging
from .errors import GuardrailViolation

logger = logging.getLogger(__name__)

def check_before_write(item: dict, config) -> None:
    """Blocks if dry_run=True (Global rule logic)."""
    if getattr(config.notion, "dry_run", False):
        raise GuardrailViolation("NW001", "dry_run=true — write blocked")

def check_max_items(count: int, config) -> None:
    """G003: hard stop if item count exceeds maximum items limit."""
    if count > getattr(config.limits, "max_items_per_run", float("inf")):
        raise GuardrailViolation(
            "G003", 
            f"Processed item count ({count}) exceeds max_items_per_run ({config.limits.max_items_per_run})"
        )

def check_api_key_not_in_log(message: str) -> str:
    """G002: redacts secrets from logs."""
    if "secret_" in message:
        return message.replace("secret_", "[REDACTED]_")
    return message
