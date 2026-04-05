"""
Skill: build_enrichment_prompt
Role: Constructs a batched LLM prompt from a list of RawItems.
Input: list[RawItem], list of valid categories
Output: str (the prompt text)
Used by: EnrichmentAgent
"""

from chromemind.schemas import RawItem


def build_enrichment_prompt(items: list[RawItem], categories: list[str]) -> str:
    """Builds a structured prompt for the LLM to enrich a batch of items."""

    category_list = ", ".join(f'"{ c}"' for c in categories)

    items_block = ""
    for i, item in enumerate(items):
        items_block += f"""
Item {i + 1}:
  title: "{item.title}"
  url: "{item.url}"
  source: "{item.source}"
  folder_path: "{item.folder_path or 'N/A'}"
  visit_count: {item.visit_count if item.visit_count is not None else 'N/A'}
"""

    prompt = f"""You are a knowledge curator assistant. Analyse each browser item below and return enrichment metadata.

VALID CATEGORIES (you MUST pick exactly one per item): [{category_list}]

ITEMS TO ENRICH:
{items_block}

For each item, return a JSON array with exactly {len(items)} objects. Each object MUST have these fields:
- "index": integer (1-based, matching the item number above)
- "category": string (one of the valid categories above)
- "summary": string (1-2 concise sentences describing what this page is about)
- "priority_score": integer 1-10 (10 = most valuable for professional growth / learning)
- "priority_reason": string (1 sentence explaining the score)
- "tags": array of 3-5 keyword strings
- "read_time_estimate": string (e.g. "5 min", "15 min", "30 min")

RULES:
- Return ONLY valid JSON. No markdown fencing, no explanation text.
- The response must be a JSON array starting with [ and ending with ].
- Do NOT assign priority_score >= 8 to more than 20% of items.
- Be concise in summaries \u2014 max 2 sentences.
- Tags should be lowercase, specific keywords (not categories).
"""

    return prompt
