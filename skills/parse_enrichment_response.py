"""
Skill: parse_enrichment_response
Role: Parses LLM JSON output into a list of enrichment dicts.
Input: raw LLM response text (str), expected count
Output: list[dict] | raises SkillError
Used by: EnrichmentAgent
"""

import json
import re
from chromemind.errors import SkillError


def parse_enrichment_response(response_text: str, expected_count: int) -> list[dict]:
    """Parses the LLM output as JSON array and validates basic structure."""

    # Strip any markdown code fencing the LLM might add despite instructions
    cleaned = response_text.strip()
    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise SkillError(f"LLM returned invalid JSON: {e}\nRaw: {response_text[:500]}")

    if not isinstance(parsed, list):
        raise SkillError(f"Expected JSON array, got {type(parsed).__name__}")

    if len(parsed) != expected_count:
        raise SkillError(
            f"Expected {expected_count} items in LLM response, got {len(parsed)}"
        )

    required_fields = {"category", "summary", "priority_score", "tags", "read_time_estimate"}
    for i, item in enumerate(parsed):
        missing = required_fields - set(item.keys())
        if missing:
            raise SkillError(
                f"Item {i + 1} missing required fields: {missing}"
            )

    return parsed
