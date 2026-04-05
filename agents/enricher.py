"""
Agent: EnrichmentAgent
Role: Batches RawItems, calls LLM for enrichment, validates output, returns EnrichedItems.
Input: list[RawItem], RunConfig
Output: list[EnrichedItem]
"""

from datetime import datetime, timezone
from chromemind.schemas import RawItem, EnrichedItem, RunConfig
from skills.build_enrichment_prompt import build_enrichment_prompt
from skills.call_llm import call_llm
from skills.parse_enrichment_response import parse_enrichment_response
from skills.validate_enrichment import validate_enrichment
from agents.logger import LoggerAgent


class EnrichmentAgent:
    @staticmethod
    def run(items: list[RawItem], config: RunConfig) -> list[EnrichedItem]:
        LoggerAgent.log(
            "enricher", "started", "info",
            {"item_count": len(items), "batch_size": config.limits.batch_size},
            config.logging
        )

        enriched: list[EnrichedItem] = []
        batch_size = config.limits.batch_size
        categories = config.enrichment.categories

        # Process in batches
        for batch_start in range(0, len(items), batch_size):
            batch = items[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1

            LoggerAgent.log(
                "enricher", f"processing_batch_{batch_num}", "debug",
                {"size": len(batch)}, config.logging
            )

            try:
                result = EnrichmentAgent._enrich_batch(batch, config, categories)
                enriched.extend(result)
                LoggerAgent.log(
                    "enricher", f"batch_{batch_num}_complete", "info",
                    {"enriched": len(result)}, config.logging
                )
            except Exception as e:
                # Mark all items in failed batch as needs_review
                LoggerAgent.log(
                    "enricher", f"batch_{batch_num}_failed", "error",
                    {"error": str(e)}, config.logging
                )
                for item in batch:
                    enriched.append(EnrichedItem(
                        **item.model_dump(),
                        category="Other",
                        summary="",
                        priority_score=5,
                        priority_reason="Enrichment failed \u2014 needs manual review",
                        tags=[],
                        read_time="Unknown",
                        enriched_at=datetime.now(timezone.utc).isoformat(),
                        needs_review=True
                    ))

        LoggerAgent.log(
            "enricher", "finished", "info",
            {
                "total_enriched": len(enriched),
                "needs_review": sum(1 for e in enriched if getattr(e, 'needs_review', False))
            },
            config.logging
        )
        return enriched

    @staticmethod
    def _enrich_batch(
        batch: list[RawItem], config: RunConfig, categories: list[str]
    ) -> list[EnrichedItem]:
        """Enriches a single batch of items via LLM."""

        prompt = build_enrichment_prompt(batch, categories)

        # Call LLM with retry
        max_retries = 1
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = call_llm(
                    prompt=prompt,
                    model=config.enrichment.model,
                    temperature=config.enrichment.temperature,
                    max_tokens=config.enrichment.max_tokens
                )

                enrichments = parse_enrichment_response(response, len(batch))
                enrichments = validate_enrichment(enrichments, categories)

                # Merge enrichment data with original RawItems
                results = []
                now = datetime.now(timezone.utc).isoformat()

                for item, enrichment in zip(batch, enrichments):
                    results.append(EnrichedItem(
                        **item.model_dump(),
                        category=enrichment["category"],
                        summary=enrichment["summary"],
                        priority_score=enrichment["priority_score"],
                        priority_reason=enrichment.get("priority_reason", ""),
                        tags=enrichment.get("tags", []),
                        read_time=enrichment.get("read_time_estimate", "Unknown"),
                        enriched_at=now
                    ))

                return results

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    continue

        raise last_error
