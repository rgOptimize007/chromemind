# ðŸ§  ChromeMind â€” Agentic Browser Knowledge Curator

> Turn your Chrome chaos (bookmarks, reading lists, tab groups) into a structured, prioritised, trackable Notion knowledge base â€” powered by agentic workflows.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [System Overview](#2-system-overview)
3. [Architecture Diagram](#3-architecture-diagram)
4. [Agent Design](#4-agent-design)
5. [Skills Catalogue](#5-skills-catalogue)
6. [Guardrails Design](#6-guardrails-design)
7. [Data Flow](#7-data-flow)
8. [Notion Schema](#8-notion-schema)
9. [Configuration Design](#9-configuration-design)
10. [Phased Build Plan](#10-phased-build-plan)
11. [Parallelism & Delegation](#11-parallelism--delegation)
12. [Repository Structure](#12-repository-structure)
13. [Learning Guide](#13-learning-guide-for-the-builder)

---

## 1. Problem Statement

Chrome power users accumulate hundreds of saved items across three siloed surfaces:

| Surface | Problem |
|---|---|
| **Bookmarks** (folders + bar) | Deeply nested, no metadata, no priority |
| **Reading List** | Linear, unread purgatory â€” nothing ever gets read |
| **Tab Groups** | Ephemeral, lost on restart, no summary |

**Result:** Knowledge graveyard. No discoverability, no prioritisation, no inference.

**Goal:** An agent-driven CLI/tool that scrapes all three surfaces, enriches each item, scores it for priority, and upserts it into a Notion database with full tracking.

---

## 2. System Overview

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚           ChromeMind CLI            â”‚  â† Entry point for the user
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                 â”‚ triggers
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚         Orchestrator Agent          â”‚  â† Master coordinator
â”‚   (reads config, delegates tasks)   â”‚
â””â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
   â”‚          â”‚          â”‚
   â–¼          â–¼          â–¼
Scraper    Enricher   Notion Writer    â† Specialised Sub-Agents
Agent      Agent      Agent
   â”‚          â”‚          â”‚
   â–¼          â–¼          â–¼
Chrome      LLM       Notion API
DevTools    Calls     (REST)
MCP
```

### Core Principles

- **Agent-driven**: No monolithic scripts. Every major concern is an agent with a defined role, input schema, output schema, and guardrails.
- **Slow start**: Phase 1 handles 10â€“50 items. The same architecture scales to 10,000+.
- **Config-first**: Everything the system does is controlled by `chromemind.config.yaml`. No hardcoded behaviour.
- **Transparent**: Every agent logs what it did, what it skipped, and why.

---

## 3. Architecture Diagram

```
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘                     ChromeMind System                        â•‘
â• â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•£
â•‘                                                              â•‘
â•‘  [User] â”€â”€â–º CLI Entry (`chromemind run`)                     â•‘
â•‘                â”‚                                             â•‘
â•‘                â–¼                                             â•‘
â•‘  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                             â•‘
â•‘  â”‚    ORCHESTRATOR AGENT        â”‚                             â•‘
â•‘  â”‚  - Reads chromemind.config   â”‚                             â•‘
â•‘  â”‚  - Decides which sources     â”‚                             â•‘
â•‘  â”‚    to scrape                 â”‚                             â•‘
â•‘  â”‚  - Spawns sub-agents         â”‚                             â•‘
â•‘  â”‚  - Aggregates results        â”‚                             â•‘
â•‘  â”‚  - Runs dedup & merge        â”‚                             â•‘
â•‘  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                             â•‘
â•‘             â”‚  delegates to                                   â•‘
â•‘      â”Œâ”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                             â•‘
â•‘      â–¼      â–¼                  â–¼                             â•‘
â•‘  â”Œâ”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”                     â•‘
â•‘  â”‚SCRAPERâ”‚ â”‚ENRICHMENTâ”‚ â”‚NOTION WRITER â”‚                     â•‘
â•‘  â”‚AGENT  â”‚ â”‚AGENT     â”‚ â”‚AGENT         â”‚                     â•‘
â•‘  â””â”€â”€â”€â”¬â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜                     â•‘
â•‘      â”‚          â”‚              â”‚                              â•‘
â•‘      â–¼          â–¼              â–¼                              â•‘
â•‘  Chrome     Gemini Pro    Notion REST API                     â•‘
â•‘  DevTools   (via SDK)     (via MCP or direct)                â•‘
â•‘  MCP                                                          â•‘
â•‘                                                              â•‘
â•‘  â”€â”€ Cross-cutting â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€     â•‘
â•‘  Logger Agent   â”‚  Guardrails Layer   â”‚  State Store          â•‘
â•‘  (every step)   â”‚  (per agent)        â”‚  (local JSON)         â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
```

---

## 4. Agent Design

Each agent has a strict contract:

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              AGENT CONTRACT                  â”‚
â”‚                                             â”‚
â”‚  role:        what this agent is             â”‚
â”‚  input:       JSON schema of what it takes   â”‚
â”‚  output:      JSON schema of what it returns â”‚
â”‚  skills:      list of skill files it uses    â”‚
â”‚  guardrails:  what it must never do          â”‚
â”‚  delegates:   sub-agents it may call         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### 4.1 Orchestrator Agent

```yaml
role: Master coordinator â€” reads config, plans execution, delegates, merges results

input:
  - chromemind.config.yaml
  - optional: --source flag (bookmarks | readinglist | tabs | all)
  - optional: --limit N (max items per source for testing)

output:
  - run_report.json  (summary of this run: counts, errors, skipped)
  - state/last_run.json (for idempotency on next run)

skills:
  - skills/parse_config.py
  - skills/plan_execution.py
  - skills/merge_results.py
  - skills/dedup.py

guardrails:
  - MUST NOT write to Notion directly â€” delegates to Notion Writer Agent
  - MUST NOT call Chrome DevTools directly â€” delegates to Scraper Agent
  - MUST respect --limit flag in all phases
  - MUST log every delegation decision

delegates:
  - ScraperAgent
  - EnrichmentAgent
  - NotionWriterAgent
  - LoggerAgent
```

---

### 4.2 Scraper Agent

```yaml
role: Extract raw items from Chrome via Chrome DevTools MCP

input:
  - sources: list (bookmarks | readinglist | tabgroups)
  - limit: int (items per source)
  - chrome_profile: path (optional)

output:
  - raw_items: list of RawItem
    - id: str (sha256 of url)
    - url: str
    - title: str
    - source: enum(bookmark|readinglist|tabgroup)
    - folder_path: str | null  (e.g. "Dev/Kafka/Articles")
    - tab_group_name: str | null
    - scraped_at: ISO timestamp

skills:
  - skills/scrape_bookmarks.py
  - skills/scrape_readinglist.py
  - skills/scrape_tabgroups.py
  - skills/normalise_raw_item.py

guardrails:
  - MUST NOT fetch page content (only metadata from Chrome)
  - MUST NOT write any files â€” returns data only
  - MUST skip duplicate URLs (by sha256 id)
  - MUST handle Chrome not being open gracefully (error, don't crash)
  - Rate limit: no more than 1 MCP call per 200ms
```

---

### 4.3 Enrichment Agent

```yaml
role: Use LLM to enrich each raw item with category, summary, and priority score

input:
  - raw_items: list of RawItem
  - enrichment_config:
      model: gemini-pro-3.1
      max_tokens: 300
      batch_size: 5  (items per LLM call)
      temperature: 0.2

output:
  - enriched_items: list of EnrichedItem
    - ...all RawItem fields
    - category: str         (e.g. "System Design", "Career", "AI/ML")
    - summary: str          (1â€“2 sentences)
    - priority_score: int   (1â€“10)
    - priority_reason: str  (why this score)
    - tags: list[str]
    - read_time_estimate: str  (e.g. "8 min")
    - enriched_at: ISO timestamp

skills:
  - skills/build_enrichment_prompt.py
  - skills/call_llm.py
  - skills/parse_enrichment_response.py
  - skills/validate_enrichment.py

guardrails:
  - MUST NOT make more than 10 LLM calls per minute (rate limit)
  - MUST validate output schema before passing downstream
  - If LLM returns invalid JSON: retry once, then mark item as needs_review=true
  - MUST NOT assign priority > 9 to more than 20% of items in a batch
    (prevents priority inflation â€” everything can't be urgent)
  - Temperature MUST stay â‰¤ 0.3 (deterministic enrichment, not creative)
```

---

### 4.4 Notion Writer Agent

```yaml
role: Upsert enriched items into the Notion database

input:
  - enriched_items: list of EnrichedItem
  - notion_config:
      database_id: str
      duplicate_strategy: enum(skip | update | create_new)
  - dry_run: bool

output:
  - write_report:
      created: int
      updated: int
      skipped: int
      failed: list[{id, reason}]

skills:
  - skills/notion_upsert.py
  - skills/map_to_notion_schema.py
  - skills/handle_notion_errors.py

guardrails:
  - If dry_run=true: MUST only log, never write
  - MUST NOT delete existing Notion pages â€” only create or update
  - MUST NOT overwrite manually-edited fields (protected_fields config)
  - Rate limit: respect Notion's 3 requests/second limit
  - On failure: log and continue, don't halt the entire run
```

---

### 4.5 Logger Agent

```yaml
role: Cross-cutting â€” every agent calls this to log actions

input:
  - agent: str
  - event: str
  - level: enum(info | warn | error)
  - payload: dict (optional)

output:
  - appends to logs/chromemind_YYYY-MM-DD.log
  - updates state/run_summary.json

skills:
  - skills/format_log_entry.py
  - skills/write_log.py

guardrails:
  - MUST NOT log sensitive data (API keys, tokens)
  - Log rotation: keep last 7 days only
```

---

## 5. Skills Catalogue

Skills are small, single-purpose Python functions that agents call. Think of them as tools in a toolbox.

```
skills/
â”œâ”€â”€ scrape_bookmarks.py        # Uses Chrome DevTools MCP to export bookmarks tree
â”œâ”€â”€ scrape_readinglist.py      # Uses Chrome DevTools MCP for reading list
â”œâ”€â”€ scrape_tabgroups.py        # Uses Chrome DevTools MCP for tab groups
â”œâ”€â”€ normalise_raw_item.py      # Converts any source item to RawItem schema
â”œâ”€â”€ dedup.py                   # sha256-based deduplication across sources
â”œâ”€â”€ build_enrichment_prompt.py # Constructs the LLM prompt for a batch of items
â”œâ”€â”€ call_llm.py                # Generic LLM caller (Gemini SDK wrapper)
â”œâ”€â”€ parse_enrichment_response.py # Parses and validates LLM JSON output
â”œâ”€â”€ validate_enrichment.py     # JSON schema validation for EnrichedItem
â”œâ”€â”€ map_to_notion_schema.py    # Maps EnrichedItem â†’ Notion page properties
â”œâ”€â”€ notion_upsert.py           # Create or update a Notion page
â”œâ”€â”€ handle_notion_errors.py    # Retry logic, error categorisation
â”œâ”€â”€ parse_config.py            # Loads and validates chromemind.config.yaml
â”œâ”€â”€ plan_execution.py          # Orchestrator: decides run order & batching
â”œâ”€â”€ merge_results.py           # Merges outputs from parallel agents
â”œâ”€â”€ format_log_entry.py        # Structured log entry formatter
â””â”€â”€ write_log.py               # File I/O for logs
```

### Skill Contract (every skill follows this)

```python
# skills/example_skill.py

"""
Skill: normalise_raw_item
Role: Converts raw scraped data into a standardised RawItem dict.
Input: dict (varies by source)
Output: RawItem dict | raises SkillError
Used by: ScraperAgent
"""

from typing import TypedDict
from chromemind.errors import SkillError

class RawItem(TypedDict):
    id: str
    url: str
    title: str
    source: str
    folder_path: str | None
    tab_group_name: str | None
    scraped_at: str

def normalise_raw_item(raw: dict, source: str) -> RawItem:
    """Single-purpose, no side effects, easy to unit test."""
    ...
```

---

## 6. Guardrails Design

Guardrails are the safety rails that prevent agents from doing unexpected things. They operate at two levels:

### 6.1 Global Guardrails (apply to all agents)

Defined in `.chromemind/global_guardrails.yaml`:

```yaml
global_guardrails:
  - id: G001
    rule: "Never delete data from Notion, only create or update"
    enforcement: hard_stop  # raises exception, halts agent

  - id: G002
    rule: "Never expose API keys in logs"
    enforcement: hard_stop

  - id: G003
    rule: "Never process more than config.max_items_per_run items total"
    enforcement: hard_stop

  - id: G004
    rule: "Always write a log entry before and after each agent action"
    enforcement: warn_and_continue

  - id: G005
    rule: "Never make outbound HTTP calls to domains not in allowlist"
    enforcement: hard_stop
    allowlist:
      - api.notion.com
      - generativelanguage.googleapis.com
```

### 6.2 Agent-Level Guardrails

Each agent's guardrails are checked by a `guardrail_check(action, context)` function called before any consequential action:

```python
# chromemind/guardrails.py

class GuardrailViolation(Exception):
    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        super().__init__(f"[GUARDRAIL {rule_id}] {message}")

def check_before_write(item: dict, config: dict) -> None:
    """Called by NotionWriterAgent before every page upsert."""
    if config.get("dry_run"):
        raise GuardrailViolation("NW001", "dry_run=true â€” write blocked")
    if item.get("manually_edited") and not config.get("allow_overwrite"):
        raise GuardrailViolation("NW002", "Protected field â€” skip update")
```

### 6.3 Priority Inflation Guardrail (Enrichment)

This is a statistical guardrail â€” it prevents the LLM from marking everything as high priority:

```python
def check_priority_distribution(batch: list[EnrichedItem]) -> None:
    high_priority = [i for i in batch if i["priority_score"] >= 8]
    if len(high_priority) / len(batch) > 0.20:
        # Re-score: compress top scores relatively
        logger.warn("GUARDRAIL EN001: Priority inflation detected. Re-normalising.")
        renormalise_scores(batch)
```

---

## 7. Data Flow

```
Chrome Browser
    â”‚
    â”‚  (Chrome DevTools MCP)
    â–¼
RawItem[]  â†â”€â”€ ScraperAgent
    â”‚
    â”‚  dedup by sha256(url)
    â–¼
RawItem[] (deduplicated)
    â”‚
    â”‚  batches of 5
    â–¼
EnrichedItem[]  â†â”€â”€ EnrichmentAgent (calls Gemini)
    â”‚
    â”‚  guardrail checks
    â–¼
NotionPage[]  â†â”€â”€ NotionWriterAgent (upserts)
    â”‚
    â–¼
Notion Database
    â”‚
    â””â”€â–º run_report.json (local state)
        logs/chromemind_YYYY-MM-DD.log
```

### State Management

Local `state/` folder tracks what's been processed:

```json
// state/last_run.json
{
  "run_id": "2026-04-02T09:00:00Z",
  "processed_ids": ["abc123", "def456"],
  "stats": {
    "scraped": 47,
    "enriched": 45,
    "written_to_notion": 45,
    "skipped_duplicate": 12,
    "failed": 2
  }
}
```

On the next run, already-processed IDs are skipped. This makes the system **idempotent** â€” safe to run multiple times.

---

## 8. Notion Schema

### Database: ChromeMind Knowledge Base

| Property | Type | Notes |
|---|---|---|
| `Title` | Title | Page title (from browser) |
| `URL` | URL | Original link |
| `Source` | Select | bookmark / readinglist / tabgroup |
| `Folder Path` | Rich Text | e.g. `Dev > Kafka > Articles` |
| `Category` | Select | LLM-assigned (e.g. "System Design") |
| `Tags` | Multi-select | LLM-assigned keywords |
| `Summary` | Rich Text | 1â€“2 sentence LLM summary |
| `Priority Score` | Number | 1â€“10 |
| `Priority Reason` | Rich Text | LLM explanation |
| `Read Time` | Rich Text | Estimated read time |
| `Status` | Select | Unread / In Progress / Done / Archived |
| `Scraped At` | Date | When ChromeMind captured this |
| `Enriched At` | Date | When LLM enriched this |
| `Needs Review` | Checkbox | Flagged if enrichment failed |
| `ChromeMind ID` | Rich Text | sha256 of URL â€” used for upserts |

---

## 9. Configuration Design

```yaml
# chromemind.config.yaml  (lives in repo root)

version: "1.0"

# â”€â”€ Sources â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
sources:
  bookmarks: true
  reading_list: true
  tab_groups: false   # start with false, enable later

# â”€â”€ Limits (for safe, slow starts) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
limits:
  max_items_per_source: 20   # Phase 1: small batches
  max_items_per_run: 50
  batch_size: 5              # items per LLM call

# â”€â”€ Enrichment â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
enrichment:
  model: "gemini-pro-3.1"
  temperature: 0.2
  max_tokens: 300
  categories:               # LLM must pick from these
    - "System Design"
    - "AI / ML"
    - "Career & Growth"
    - "Finance"
    - "Productivity"
    - "Health"
    - "Entertainment"
    - "Other"

# â”€â”€ Notion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
notion:
  database_id: "${NOTION_DATABASE_ID}"   # from .env
  duplicate_strategy: "update"           # skip | update | create_new
  protected_fields:                      # never overwrite these
    - "Status"
    - "Notes"
  dry_run: false

# â”€â”€ Guardrails â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
guardrails:
  max_high_priority_percent: 20   # priority inflation check
  allowed_domains:
    - "api.notion.com"
    - "generativelanguage.googleapis.com"

# â”€â”€ Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
logging:
  level: "info"    # debug | info | warn | error
  retain_days: 7

# â”€â”€ Chrome â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
chrome:
  profile: "Default"
  mcp_timeout_ms: 5000
```

---

## 10. Phased Build Plan

### Phase 1 â€” Foundation (Week 1â€“2)
**Goal:** Get 10 bookmarks into Notion manually triggered.

- [ ] Set up repo structure
- [ ] Write `chromemind.config.yaml` schema + parser skill
- [ ] Implement ScraperAgent (bookmarks only, limit 10)
- [ ] Implement Logger Agent
- [ ] Implement Notion Writer Agent (dry_run first)
- [ ] Wire Orchestrator Agent to call all three
- [ ] CLI: `chromemind run --source bookmarks --limit 10 --dry-run`

**Learning focus:** Agent contracts, skill pattern, config loading, local state.

---

### Phase 2 â€” Enrichment (Week 3)
**Goal:** LLM assigns categories and priorities before writing to Notion.

- [ ] Implement Enrichment Agent
- [ ] Build prompt template for batch enrichment
- [ ] Add priority inflation guardrail
- [ ] Validate enrichment output schema
- [ ] End-to-end: scrape â†’ enrich â†’ write 10 items

**Learning focus:** LLM prompt design, guardrails, output validation, retry logic.

---

### Phase 3 â€” All Sources + Dedup (Week 4)
**Goal:** Handle all three Chrome sources without duplicates.

- [ ] Add Reading List scraper skill
- [ ] Add Tab Group scraper skill
- [ ] Implement dedup by sha256 URL
- [ ] Implement idempotent runs via `state/last_run.json`
- [ ] Test with 50 items across all sources

**Learning focus:** Idempotency, cross-source dedup, state management.

---

### Phase 4 â€” Parallelism & Scale (Week 5+)
**Goal:** Run enrichment and writing in parallel for large sets.

- [ ] Orchestrator spawns Enrichment + Write agents in parallel batches
- [ ] Add rate limiting middleware
- [ ] Test with 200+ items
- [ ] Add `--since` flag: only process items scraped after a date

**Learning focus:** Parallelism, delegation, rate limiting.

---

## 11. Parallelism & Delegation

### How the Orchestrator delegates

```
Orchestrator
â”‚
â”œâ”€â–º ScraperAgent (sequential â€” Chrome MCP is single-threaded)
â”‚       â”‚
â”‚       â””â”€â–º returns RawItem[50]
â”‚
â”œâ”€â–º splits into 10 batches of 5 items
â”‚
â”œâ”€â–º EnrichmentAgent Ã— 10  (parallel â€” independent LLM calls)
â”‚       â”‚   â”‚   â”‚
â”‚       â–¼   â–¼   â–¼
â”‚      [batch1][batch2]...[batch10]
â”‚
â”œâ”€â–º merges 10 EnrichedItem lists
â”‚
â””â”€â–º NotionWriterAgent (sequential â€” Notion rate limit: 3 req/s)
```

### Delegation Pattern in Code

```python
# agents/orchestrator.py

import asyncio
from agents import ScraperAgent, EnrichmentAgent, NotionWriterAgent

async def run(config):
    # Phase 1: Scrape (sequential)
    raw_items = await ScraperAgent.run(config)
    
    # Phase 2: Enrich (parallel batches)
    batches = chunk(raw_items, config.limits.batch_size)
    enrich_tasks = [EnrichmentAgent.run(batch, config) for batch in batches]
    enriched_batches = await asyncio.gather(*enrich_tasks)
    enriched_items = flatten(enriched_batches)
    
    # Phase 3: Write (sequential, rate-limited)
    report = await NotionWriterAgent.run(enriched_items, config)
    
    return report
```

---

## 12. Repository Structure

```
chromemind/
â”‚
â”œâ”€â”€ README.md                    â† Quick start for GitHub users
â”œâ”€â”€ SYSTEM_DESIGN.md             â† This document
â”œâ”€â”€ chromemind.config.yaml       â† Main config (users edit this)
â”œâ”€â”€ chromemind.config.schema.yaml â† JSON schema for validation
â”œâ”€â”€ .env.example                 â† Template: NOTION_TOKEN, DATABASE_ID
â”œâ”€â”€ pyproject.toml               â† Dependencies
â”‚
â”œâ”€â”€ chromemind/                  â† Core package
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ cli.py                   â† `chromemind run` entry point
â”‚   â”œâ”€â”€ errors.py                â† Custom exceptions
â”‚   â”œâ”€â”€ guardrails.py            â† Guardrail checks
â”‚   â””â”€â”€ schemas.py               â† RawItem, EnrichedItem TypedDicts
â”‚
â”œâ”€â”€ agents/                      â† One file per agent
â”‚   â”œâ”€â”€ orchestrator.py
â”‚   â”œâ”€â”€ scraper.py
â”‚   â”œâ”€â”€ enrichment.py
â”‚   â”œâ”€â”€ notion_writer.py
â”‚   â””â”€â”€ logger.py
â”‚
â”œâ”€â”€ skills/                      â† Single-purpose skill functions
â”‚   â”œâ”€â”€ scrape_bookmarks.py
â”‚   â”œâ”€â”€ scrape_readinglist.py
â”‚   â”œâ”€â”€ scrape_tabgroups.py
â”‚   â”œâ”€â”€ normalise_raw_item.py
â”‚   â”œâ”€â”€ dedup.py
â”‚   â”œâ”€â”€ build_enrichment_prompt.py
â”‚   â”œâ”€â”€ call_llm.py
â”‚   â”œâ”€â”€ parse_enrichment_response.py
â”‚   â”œâ”€â”€ validate_enrichment.py
â”‚   â”œâ”€â”€ map_to_notion_schema.py
â”‚   â”œâ”€â”€ notion_upsert.py
â”‚   â”œâ”€â”€ handle_notion_errors.py
â”‚   â”œâ”€â”€ parse_config.py
â”‚   â”œâ”€â”€ plan_execution.py
â”‚   â”œâ”€â”€ merge_results.py
â”‚   â””â”€â”€ write_log.py
â”‚
â”œâ”€â”€ prompts/                     â† LLM prompt templates
â”‚   â””â”€â”€ enrich_batch.txt         â† The enrichment prompt
â”‚
â”œâ”€â”€ state/                       â† Runtime state (gitignored)
â”‚   â””â”€â”€ last_run.json
â”‚
â”œâ”€â”€ logs/                        â† Rotated logs (gitignored)
â”‚
â””â”€â”€ tests/                       â† Unit tests per skill
    â”œâ”€â”€ test_dedup.py
    â”œâ”€â”€ test_enrichment_parse.py
    â”œâ”€â”€ test_guardrails.py
    â””â”€â”€ fixtures/
        â””â”€â”€ sample_raw_items.json
```

---

## 13. Learning Guide for the Builder

This section maps your stated learning goals to concrete things you'll build.

### ðŸŽ¯ What you'll learn and where

| Concept | Where you'll build it | What to observe |
|---|---|---|
| **Agent contracts** | `agents/` â€” each agent file | Input schema â†’ output schema â†’ no leakage between agents |
| **Skills pattern** | `skills/` â€” every .py file | Single purpose, no side effects, unit-testable |
| **Guardrails** | `chromemind/guardrails.py` | Hard stops vs. warn-and-continue |
| **Global vs repo-level instructions** | `.chromemind/global_guardrails.yaml` + `chromemind.config.yaml` | Config at different layers |
| **Prompt design** | `prompts/enrich_batch.txt` | Structured output, temperature, batch design |
| **Parallelism** | `agents/orchestrator.py` | `asyncio.gather` for enrichment batches |
| **Delegation** | Orchestrator â†’ sub-agents | Agent calls agent, not function calls |
| **Idempotency** | `state/last_run.json` + dedup skill | Running twice = same result |
| **State management** | `state/` folder | What to persist, what to recompute |
| **Documentation sub-agent** | You can add a DocAgent in Phase 4 | Agent that writes markdown summaries of Notion DB state |

### ðŸ”‘ Key mental models

**Agents vs Skills:**
- An **Agent** has a role, makes decisions, calls other agents or skills, has guardrails.
- A **Skill** is a dumb function â€” no decisions, no side effects, just transforms data.

**Guardrails vs Validation:**
- **Validation** = "is this data the right shape?" (schema check)
- **Guardrail** = "is this action safe to take?" (policy check)

**Global vs Agent-level config:**
- **Global** = applies regardless of which agent runs (API key safety, max items)
- **Agent-level** = specific to that agent's job (enrichment temperature, notion protected fields)

---

*ChromeMind â€” Version 1.0 | Start small, think in agents, build for scale.*