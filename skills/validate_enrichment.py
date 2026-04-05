"""
Skill: validate_enrichment
Role: Validates enriched items against schema and checks priority inflation guardrail.
Input: list of enrichment dicts, valid categories
Output: list of validated dicts (with clamped scores if needed)
Used by: EnrichmentAgent
"""

import logging

logger = logging.getLogger(__name__)


def validate_enrichment(enrichments: list[dict], valid_categories: list[str]) -> list[dict]:
    """Validates and sanitises LLM enrichment output."""

    for item in enrichments:
        # Clamp priority_score to 1-10
        score = item.get("priority_score", 5)
        if not isinstance(score, int):
            try:
                score = int(score)
            except (ValueError, TypeError):
                score = 5
        item["priority_score"] = max(1, min(10, score))

        # Validate category \u2014 fallback to "Other" if not in allowed list
        if item.get("category") not in valid_categories:
            logger.warning(
                f"Invalid category '{item.get('category')}', falling back to 'Other'"
            )
            item["category"] = "Other"

        # Ensure tags is a list of strings
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        item["tags"] = [str(t).lower().strip() for t in tags[:5]]

        # Ensure summary is a string
        if not isinstance(item.get("summary"), str):
            item["summary"] = ""

        # Ensure read_time_estimate is a string
        if not isinstance(item.get("read_time_estimate"), str):
            item["read_time_estimate"] = "Unknown"

        # Ensure priority_reason is a string
        if not isinstance(item.get("priority_reason"), str):
            item["priority_reason"] = ""

    # Priority inflation guardrail (EN001)
    _check_priority_inflation(enrichments)

    return enrichments


def _check_priority_inflation(enrichments: list[dict], threshold: float = 0.20) -> None:
    """If more than 20% of items have priority >= 8, compress high scores."""
    if not enrichments:
        return

    high_priority = [e for e in enrichments if e["priority_score"] >= 8]
    ratio = len(high_priority) / len(enrichments)

    if ratio > threshold:
        logger.warning(
            f"GUARDRAIL EN001: Priority inflation detected "
            f"({len(high_priority)}/{len(enrichments)} = {ratio:.0%} >= 8). "
            f"Re-normalising scores."
        )
        # Sort by score descending, keep only top 20% as high
        sorted_items = sorted(enrichments, key=lambda x: x["priority_score"], reverse=True)
        max_high = max(1, int(len(enrichments) * threshold))

        for item in sorted_items[max_high:]:
            if item["priority_score"] >= 8:
                item["priority_score"] = 7
