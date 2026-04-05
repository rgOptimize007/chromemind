# 🧠 ChromeMind — Agentic Browser Knowledge Curator

> Turn your Chrome chaos (bookmarks, history, active tabs) into a structured, prioritised, trackable **Notion knowledge base** — powered by agentic workflows and LLM enrichment.

---

## ✨ Features

- **Multi-source scraping** — Bookmarks, browsing history, and active tabs
- **LLM enrichment** — Auto-categorise, summarise, tag, and priority-score every item using Gemini
- **Notion sync** — Idempotent upserts with deduplication (sha256-based)
- **Guardrails** — Priority inflation detection, rate limiting, dry-run mode, never-delete policy
- **Agent architecture** — Modular agents (Scraper → Enricher → Writer) with structured logging

---

## 🏗 Architecture

```
┌─────────────────────────────────┐
│         ChromeMind CLI          │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│       Orchestrator Agent        │
└──┬───────────┬──────────┬───────┘
   │           │          │
   ▼           ▼          ▼
Scraper    Enrichment   Notion Writer
Agent      Agent        Agent
   │           │          │
   ▼           ▼          ▼
Chrome      Gemini     Notion API
Files/DB    LLM        (REST)
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **CLI** | [Click](https://click.palletsprojects.com/) |
| **Config** | YAML + `.env` (via `python-dotenv`) |
| **Validation** | [Pydantic v2](https://docs.pydantic.dev/) |
| **LLM** | [Google Gemini](https://ai.google.dev/) via `google-genai` SDK |
| **Notion** | [notion-client](https://github.com/ramnes/notion-sdk-py) (REST API) |
| **Browser Data** | Chrome Bookmarks JSON, History SQLite, DevTools Protocol |
| **Testing** | pytest + pytest-asyncio |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Google Chrome installed
- A Notion integration token ([Create one here](https://www.notion.so/my-integrations))
- A Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Setup

```bash
# Clone the repository
git clone https://github.com/rgOptimize007/chromemind.git
cd chromemind

# Install in development mode
pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your actual keys (see Configuration below)
```

---

## ⚙️ Configuration

### 1. Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your values:

```env
NOTION_TOKEN=secret_your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id_here
GEMINI_API_KEY=your_gemini_api_key_here
```

| Variable | Description | How to get it |
|---|---|---|
| `NOTION_TOKEN` | Notion integration API token | [Notion Integrations](https://www.notion.so/my-integrations) → Create new → Copy token |
| `NOTION_DATABASE_ID` | Target Notion database ID | Open database in browser → copy 32-char hex from URL |
| `GEMINI_API_KEY` | Google Gemini API key | [AI Studio](https://aistudio.google.com/apikey) → Create API key |

### 2. Config File (`chromemind-config.yaml`)

The main config file controls all pipeline behaviour.
> [!IMPORTANT]
> The `chromemind-config.yaml` is ignored by git to protect your privacy. Use the provided template to get started:
> ```bash
> cp chromemind-config.example.yaml chromemind-config.yaml
> ```

Key sections in `chromemind-config.yaml`:

```yaml
sources:
  bookmarks: true        # Scrape Chrome bookmarks
  history: true          # Scrape browsing history
  tab_groups: false      # Scrape active tabs (requires Chrome debug mode)

limits:
  max_items_per_source: 500
  max_items_per_run: 1000
  batch_size: 5          # Items per LLM enrichment call

enrichment:
  model: "gemini-2.5-flash"
  temperature: 0.2
  categories:            # LLM picks from these
    - "System Design"
    - "AI / ML"
    - "Career & Growth"
    # ... add your own

chrome:
  profile: "Default"     # Your Chrome profile directory name
  history_days: 1        # How many days of history to import
```

### 3. Notion Database Setup

Your Notion database needs these properties (they're created automatically on first run):

| Property | Type | Description |
|---|---|---|
| Name | Title | Page title from browser |
| URL | URL | Original link |
| Source | Select | `bookmark` / `history` / `tab` |
| Category | Select | LLM-assigned category |
| Tags | Multi-select | LLM-assigned keywords |
| Summary | Rich Text | 1-2 sentence LLM summary |
| Priority Score | Number | 1-10 importance rating |
| Priority Reason | Rich Text | Why this score |
| Read Time | Rich Text | Estimated reading time |
| Status | Select | `Unread` / `In Progress` / `Done` |
| ChromeMind ID | Rich Text | SHA256 hash for deduplication |
| Timestamp | Date | When item was scraped |
| Enriched At | Date | When LLM enriched the item |
| Needs Review | Checkbox | Flagged if enrichment failed |

> **Important:** Share your Notion database with your integration: Database → `...` → "Add connections" → select your integration name.

### 4. Chrome Profile

Find your Chrome profile name:

```bash
# Windows
ls "$env:LOCALAPPDATA\Google\Chrome\User Data" | Select-String "Profile|Default"

# macOS
ls ~/Library/Application\ Support/Google/Chrome/ | grep -E "Profile|Default"
```

Set the profile name in `chromemind-config.yaml` under `chrome.profile`.

---

## 🚀 Usage

### Basic Commands

```bash
# Scrape + Enrich + Write to Notion (default)
chromemind run --source bookmarks --limit 10

# Scrape bookmarks without enrichment
chromemind run --source bookmarks --limit 10 --no-enrich

# Dry run (scrape + enrich, but don't write to Notion)
chromemind run --source bookmarks --limit 10 --dry-run

# Scrape all sources
chromemind run --source all

# Scrape today's history
chromemind run --source history --limit 100

# Scrape active tabs (Chrome must be in debug mode)
chromemind run --source tabs
```

### Active Tabs (requires Chrome debug mode)

To scrape active tabs, Chrome must be launched with remote debugging:

```bash
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### CLI Options

| Option | Default | Description |
|---|---|---|
| `--source` | `all` | `bookmarks`, `history`, `tabs`, or `all` |
| `--limit` | from config | Max items per source |
| `--enrich / --no-enrich` | `--enrich` | Enable/disable LLM enrichment |
| `--dry-run / --no-dry-run` | from config | Skip Notion writes |

---

## 📁 Project Structure

```
chromemind/
├── chromemind/                # Core package
│   ├── __init__.py
│   ├── cli.py                 # Click CLI entry point
│   ├── schemas.py             # Pydantic models (RawItem, EnrichedItem, etc.)
│   ├── errors.py              # Custom exceptions
│   └── guardrails.py          # Safety checks (dry-run, max items, etc.)
│
├── agents/                    # Agent layer
│   ├── orchestrator.py        # Master coordinator
│   ├── scraper.py             # Multi-source scraper
│   ├── enricher.py            # LLM enrichment agent
│   ├── notion_writer.py       # Notion upsert agent
│   └── logger.py              # Structured logging agent
│
├── skills/                    # Skill layer (single-purpose functions)
│   ├── parse_config.py        # YAML + env var config loader
│   ├── scrape_bookmarks.py    # Chrome Bookmarks JSON parser
│   ├── scrape_history.py      # Chrome History SQLite reader
│   ├── scrape_tabs.py         # Chrome DevTools Protocol tab scraper
│   ├── normalise_raw_item.py  # Unified item normaliser + SHA256 ID
│   ├── build_enrichment_prompt.py  # LLM prompt builder
│   ├── call_llm.py            # Gemini SDK wrapper with retry
│   ├── parse_enrichment_response.py # LLM JSON output parser
│   ├── validate_enrichment.py # Schema validation + priority guardrail
│   ├── map_to_notion_schema.py # RawItem/EnrichedItem → Notion properties
│   ├── notion_upsert.py       # Create/update Notion pages
│   ├── handle_notion_errors.py # Retry + error handling for Notion API
│   ├── format_log_entry.py    # Structured JSON log formatter
│   └── write_log.py           # Log file writer with rotation
│
├── .chromemind/               # Guardrail definitions
│   └── global_guardrails.yaml
│
├── state/                     # Run state (gitignored)
├── logs/                      # Daily logs (gitignored)
│
├── chromemind-config.example.yaml # Configuration template
├── .env.example               # Environment template
├── .gitignore
├── pyproject.toml             # Package definition
├── SYSTEM_DESIGN.md           # Full architecture specification
└── README.md
```

---

## 🛡 Guardrails

ChromeMind enforces safety at every layer:

| ID | Rule | Enforcement |
|---|---|---|
| G001 | Never delete data from Notion | Hard stop |
| G002 | Never expose API keys in logs | Hard stop |
| G003 | Never exceed `max_items_per_run` | Hard stop |
| G004 | Log before and after every agent action | Warn |
| G005 | Only call allowed domains | Hard stop |
| EN001 | No more than 20% of items can have priority ≥ 8 | Auto-compress scores |

---

## 📊 How It Works

1. **Scrape** — Reads Chrome's local `Bookmarks` JSON file and `History` SQLite database (copies to temp to avoid locking). Active tabs use Chrome DevTools Protocol.

2. **Normalise** — Each item gets a deterministic `id = sha256(url)` for deduplication across sources.

3. **Enrich** — Items are batched (default 5/batch) and sent to Gemini for categorisation, summarisation, priority scoring, tagging, and read-time estimation.

4. **Validate** — LLM output is validated: categories must be from the allowed list, priority scores are clamped 1-10, and the priority inflation guardrail triggers if >20% score ≥8.

5. **Write** — Idempotent upserts to Notion: existing pages (matched by `ChromeMind ID`) are updated, new ones are created. Protected fields (Status, Notes) are never overwritten.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is for personal use. See [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for the full architecture specification.
