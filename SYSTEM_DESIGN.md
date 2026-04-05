# 🧠 ChromeMind — Agentic Browser Knowledge Curator

> Turn your Chrome chaos (bookmarks, reading lists, tab groups) into a structured, prioritised, trackable Notion knowledge base — powered by agentic workflows.

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
| **Reading List** | Linear, unread purgatory — nothing ever gets read |
| **Tab Groups** | Ephemeral, lost on restart, no summary |

**Result:** Knowledge graveyard. No discoverability, no prioritisation, no inference.

**Goal:** An agent-driven CLI/tool that scrapes all three surfaces, enriches each item, scores it for priority, and upserts it into a Notion database with full tracking.

---

## 2. System Overview

```
┌─────────────────────────────────────┐
│           ChromeMind CLI            │  ← Entry point for the user
└────────────────┬────────────────────┘
                 │ triggers
┌────────────────▼────────────────────┐
│         Orchestrator Agent          │  ← Master coordinator
│   (reads config, delegates tasks)   │
└──┬──────────┬──────────┬────────────┘
   │          │          │
   ▼          ▼          ▼
Scraper    Enricher   Notion Writer    ← Specialised Sub-Agents
Agent      Agent      Agent
   │          │          │
   ▼          ▼          ▼
Chrome      LLM       Notion API
DevTools    Calls     (REST)
MCP
```

### Core Principles

- **Agent-driven**: No monolithic scripts. Every major concern is an agent with a defined role, input schema, output schema, and guardrails.
- **Slow start**: Phase 1 handles 10–50 items. The same architecture scales to 10,000+.
- **Config-first**: Everything the system does is controlled by `chromemind.config.yaml`. No hardcoded behaviour.
- **Transparent**: Every agent logs what it did, what it skipped, and why.

---

## 3. Architecture Diagram

```
╔══════════════════════════════════════════════════════════════╗
║                     ChromeMind System                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  [User] ──► CLI Entry (`chromemind run`)                     ║
║                │                                             ║
║                ▼                                             ║
║  ┌─────────────────────────────┐                             ║
║  │    ORCHESTRATOR AGENT        │                             ║
║  │  - Reads chromemind.config   │                             ║
║  │  - Decides which sources     │                             ║
║  │    to scrape                 │                             ║
║  │  - Spawns sub-agents         │                             ║
║  │  - Aggregates results        │                             ║
║  │  - Runs dedup & merge        │                             ║
║  └──────────┬──────────────────┘                             ║
║             │  delegates to                                   ║
║      ┌──────┼──────────────────┐                             ║
║      ▼      ▼                  ▼                             ║
║  ┌───────┐ ┌──────────┐ ┌──────────────┐                     ║
║  │SCRAPER│ │ENRICHMENT│ │NOTION WRITER │                     ║
║  │AGENT  │ │AGENT     │ │AGENT         │                     ║
║  └───┬───┘ └────┬─────┘ └──────┬───────┘                     ║
║      │          │              │                              ║
║      ▼          ▼              ▼                              ║
║  Chrome     Gemini Pro    Notion REST API                     ║
║  DevTools   (via SDK)     (via MCP or direct)                ║
║  MCP                                                          ║
║                                                              ║
║  ── Cross-cutting ──────────────────────────────────────     ║
║  Logger Agent   │  Guardrails Layer   │  State Store          ║
║  (every step)   │  (per agent)        │  (local JSON)         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 4. Agent Design

Each agent has a strict contract:

```
┌─────────────────────────────────────────────┐
│              AGENT CONTRACT                  │
│                                             │
│  role:        what this agent is             │
│  input:       JSON schema of what it takes   │
│  output:      JSON schema of what it returns │
│  skills:      list of skill files it uses    │
│  guardrails:  what it must never do          │
│  delegates:   sub-agents it may call         │
└─────────────────────────────────────────────┘
```

### 4.1 Orchestrator Agent

```yaml
role: Master coordinator — reads config, plans execution, delegates, merges results

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
  - MUST NOT write to Notion directly — delegates to Notion Writer Agent
  - MUST NOT call Chrome DevTools directly — delegates to Scraper Agent
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
  - MUST NOT write any files — returns data only
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
    - summary: str          (1–2 sentences)
    - priority_score: int   (1–10)
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
    (prevents priority inflation — everything can't be urgent)
  - Temperature MUST stay ≤ 0.3 (deterministic enrichment, not creative)
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
  - MUST NOT delete existing Notion pages — only create or update
  - MUST NOT overwrite manually-edited fields (protected_fields config)
  - Rate limit: respect Notion's 3 requests/second limit
  - On failure: log and continue, don't halt the entire run
```

---

### 4.5 Logger Agent

```yaml
role: Cross-cutting — every agent calls this to log actions

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
├── scrape_bookmarks.py        # Uses Chrome DevTools MCP to export bookmarks tree
├── scrape_readinglist.py      # Uses Chrome DevTools MCP for reading list
├── scrape_tabgroups.py        # Uses Chrome DevTools MCP for tab groups
├── normalise_raw_item.py      # Converts any source item to RawItem schema
├── dedup.py                   # sha256-based deduplication across sources
├── build_enrichment_prompt.py # Constructs the LLM prompt for a batch of items
├── call_llm.py                # Generic LLM caller (Gemini SDK wrapper)
├── parse_enrichment_response.py # Parses and validates LLM JSON output
├── validate_enrichment.py     # JSON schema validation for EnrichedItem
├── map_to_notion_schema.py    # Maps EnrichedItem → Notion page properties
├── notion_upsert.py           # Create or update a Notion page
├── handle_notion_errors.py    # Retry logic, error categorisation
├── parse_config.py            # Loads and validates chromemind.config.yaml
├── plan_execution.py          # Orchestrator: decides run order & batching
├── merge_results.py           # Merges outputs from parallel agents
├── format_log_entry.py        # Structured log entry formatter
└── write_log.py               # File I/O for logs
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
        raise GuardrailViolation("NW001", "dry_run=true — write blocked")
    if item.get("manually_edited") and not config.get("allow_overwrite"):
        raise GuardrailViolation("NW002", "Protected field — skip update")
```

### 6.3 Priority Inflation Guardrail (Enrichment)

This is a statistical guardrail — it prevents the LLM from marking everything as high priority:

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
    │
    │  (Chrome DevTools MCP)
    ▼
RawItem[]  ←── ScraperAgent
    │
    │  dedup by sha256(url)
    ▼
RawItem[] (deduplicated)
    │
    │  batches of 5
    ▼
EnrichedItem[]  ←── EnrichmentAgent (calls Gemini)
    │
    │  guardrail checks
    ▼
NotionPage[]  ←── NotionWriterAgent (upserts)
    │
    ▼
Notion Database
    │
    └─► run_report.json (local state)
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

On the next run, already-processed IDs are skipped. This makes the system **idempotent** — safe to run multiple times.

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
| `Summary` | Rich Text | 1–2 sentence LLM summary |
| `Priority Score` | Number | 1–10 |
| `Priority Reason` | Rich Text | LLM explanation |
| `Read Time` | Rich Text | Estimated read time |
| `Status` | Select | Unread / In Progress / Done / Archived |
| `Scraped At` | Date | When ChromeMind captured this |
| `Enriched At` | Date | When LLM enriched this |
| `Needs Review` | Checkbox | Flagged if enrichment failed |
| `ChromeMind ID` | Rich Text | sha256 of URL — used for upserts |

---

## 9. Configuration Design

```yaml
# chromemind.config.yaml  (lives in repo root)

version: "1.0"

# ── Sources ──────────────────────────────────────────
sources:
  bookmarks: true
  reading_list: true
  tab_groups: false   # start with false, enable later

# ── Limits (for safe, slow starts) ───────────────────
limits:
  max_items_per_source: 20   # Phase 1: small batches
  max_items_per_run: 50
  batch_size: 5              # items per LLM call

# ── Enrichment ────────────────────────────────────────
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

# ── Notion ────────────────────────────────────────────
notion:
  database_id: "${NOTION_DATABASE_ID}"   # from .env
  duplicate_strategy: "update"           # skip | update | create_new
  protected_fields:                      # never overwrite these
    - "Status"
    - "Notes"
  dry_run: false

# ── Guardrails ────────────────────────────────────────
guardrails:
  max_high_priority_percent: 20   # priority inflation check
  allowed_domains:
    - "api.notion.com"
    - "generativelanguage.googleapis.com"

# ── Logging ───────────────────────────────────────────
logging:
  level: "info"    # debug | info | warn | error
  retain_days: 7

# ── Chrome ────────────────────────────────────────────
chrome:
  profile: "Default"
  mcp_timeout_ms: 5000
```

---

## 10. Phased Build Plan

### Phase 1 — Foundation (Week 1–2)
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

### Phase 2 — Enrichment (Week 3)
**Goal:** LLM assigns categories and priorities before writing to Notion.

- [ ] Implement Enrichment Agent
- [ ] Build prompt template for batch enrichment
- [ ] Add priority inflation guardrail
- [ ] Validate enrichment output schema
- [ ] End-to-end: scrape → enrich → write 10 items

**Learning focus:** LLM prompt design, guardrails, output validation, retry logic.

---

### Phase 3 — All Sources + Dedup (Week 4)
**Goal:** Handle all three Chrome sources without duplicates.

- [ ] Add Reading List scraper skill
- [ ] Add Tab Group scraper skill
- [ ] Implement dedup by sha256 URL
- [ ] Implement idempotent runs via `state/last_run.json`
- [ ] Test with 50 items across all sources

**Learning focus:** Idempotency, cross-source dedup, state management.

---

### Phase 4 — Parallelism & Scale (Week 5+)
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
│
├─► ScraperAgent (sequential — Chrome MCP is single-threaded)
│       │
│       └─► returns RawItem[50]
│
├─► splits into 10 batches of 5 items
│
├─► EnrichmentAgent × 10  (parallel — independent LLM calls)
│       │   │   │
│       ▼   ▼   ▼
│      [batch1][batch2]...[batch10]
│
├─► merges 10 EnrichedItem lists
│
└─► NotionWriterAgent (sequential — Notion rate limit: 3 req/s)
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
│
├── README.md                    ← Quick start for GitHub users
├── SYSTEM_DESIGN.md             ← This document
├── chromemind.config.yaml       ← Main config (users edit this)
├── chromemind.config.schema.yaml ← JSON schema for validation
├── .env.example                 ← Template: NOTION_TOKEN, DATABASE_ID
├── pyproject.toml               ← Dependencies
│
├── chromemind/                  ← Core package
│   ├── __init__.py
│   ├── cli.py                   ← `chromemind run` entry point
│   ├── errors.py                ← Custom exceptions
│   ├── guardrails.py            ← Guardrail checks
│   └── schemas.py               ← RawItem, EnrichedItem TypedDicts
│
├── agents/                      ← One file per agent
│   ├── orchestrator.py
│   ├── scraper.py
│   ├── enrichment.py
│   ├── notion_writer.py
│   └── logger.py
│
├── skills/                      ← Single-purpose skill functions
│   ├── scrape_bookmarks.py
│   ├── scrape_readinglist.py
│   ├── scrape_tabgroups.py
│   ├── normalise_raw_item.py
│   ├── dedup.py
│   ├── build_enrichment_prompt.py
│   ├── call_llm.py
│   ├── parse_enrichment_response.py
│   ├── validate_enrichment.py
│   ├── map_to_notion_schema.py
│   ├── notion_upsert.py
│   ├── handle_notion_errors.py
│   ├── parse_config.py
│   ├── plan_execution.py
│   ├── merge_results.py
│   └── write_log.py
│
├── prompts/                     ← LLM prompt templates
│   └── enrich_batch.txt         ← The enrichment prompt
│
├── state/                       ← Runtime state (gitignored)
│   └── last_run.json
│
├── logs/                        ← Rotated logs (gitignored)
│
└── tests/                       ← Unit tests per skill
    ├── test_dedup.py
    ├── test_enrichment_parse.py
    ├── test_guardrails.py
    └── fixtures/
        └── sample_raw_items.json
```

---

## 13. Learning Guide for the Builder

This section maps your stated learning goals to concrete things you'll build.

### 🎯 What you'll learn and where

| Concept | Where you'll build it | What to observe |
|---|---|---|
| **Agent contracts** | `agents/` — each agent file | Input schema → output schema → no leakage between agents |
| **Skills pattern** | `skills/` — every .py file | Single purpose, no side effects, unit-testable |
| **Guardrails** | `chromemind/guardrails.py` | Hard stops vs. warn-and-continue |
| **Global vs repo-level instructions** | `.chromemind/global_guardrails.yaml` + `chromemind.config.yaml` | Config at different layers |
| **Prompt design** | `prompts/enrich_batch.txt` | Structured output, temperature, batch design |
| **Parallelism** | `agents/orchestrator.py` | `asyncio.gather` for enrichment batches |
| **Delegation** | Orchestrator → sub-agents | Agent calls agent, not function calls |
| **Idempotency** | `state/last_run.json` + dedup skill | Running twice = same result |
| **State management** | `state/` folder | What to persist, what to recompute |
| **Documentation sub-agent** | You can add a DocAgent in Phase 4 | Agent that writes markdown summaries of Notion DB state |

### 🔑 Key mental models

**Agents vs Skills:**
- An **Agent** has a role, makes decisions, calls other agents or skills, has guardrails.
- A **Skill** is a dumb function — no decisions, no side effects, just transforms data.

**Guardrails vs Validation:**
- **Validation** = "is this data the right shape?" (schema check)
- **Guardrail** = "is this action safe to take?" (policy check)

**Global vs Agent-level config:**
- **Global** = applies regardless of which agent runs (API key safety, max items)
- **Agent-level** = specific to that agent's job (enrichment temperature, notion protected fields)

---

*ChromeMind — Version 1.0 | Start small, think in agents, build for scale.*