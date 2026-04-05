from typing import Literal, Any
from pydantic import BaseModel, ConfigDict, Field

class RawItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str
    title: str
    source: Literal["bookmark", "history", "tab"]
    folder_path: str | None = None
    scraped_at: str
    visit_count: int | None = None
    tab_group_name: str | None = None

class EnrichedItem(RawItem):
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    summary: str | None = None
    priority_score: int | None = None
    priority_reason: str | None = None
    read_time: str | None = None
    enriched_at: str | None = None
    needs_review: bool = False

class RunConfigLimits(BaseModel):
    max_items_per_source: int
    max_items_per_run: int
    batch_size: int

class RunConfigEnrichment(BaseModel):
    model: str
    temperature: float
    max_tokens: int
    categories: list[str]

class RunConfigNotion(BaseModel):
    database_id: str
    duplicate_strategy: Literal["skip", "update", "create_new"]
    protected_fields: list[str]
    dry_run: bool

class RunConfigGuardrails(BaseModel):
    max_high_priority_percent: int
    allowed_domains: list[str]

class RunConfigSources(BaseModel):
    bookmarks: bool
    reading_list: bool
    tab_groups: bool
    history: bool

class RunConfigLogging(BaseModel):
    level: Literal["debug", "info", "warn", "error"]
    retain_days: int

class RunConfigChrome(BaseModel):
    profile: str
    mcp_timeout_ms: int
    remote_debug_port: int
    history_days: int

class RunConfig(BaseModel):
    version: str
    sources: RunConfigSources
    limits: RunConfigLimits
    enrichment: RunConfigEnrichment
    notion: RunConfigNotion
    guardrails: RunConfigGuardrails
    logging: RunConfigLogging
    chrome: RunConfigChrome

class WriteReport(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: list[dict[str, str]] = Field(default_factory=list)
