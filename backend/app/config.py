from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite://"
    seed_file: str = "mock-data/prospects.json"
    data_source: str = "synthetic"
    # LLM providers — multi-provider governance (Claude → Gemini → rule-based)
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    copilot_model: str = "claude-haiku-4-5-20251001"
    gemini_model: str = "gemini-1.5-flash"
    # CPaaS
    cpaas_webhook_url: str = ""
    # IDBI sandbox
    idbi_sandbox_base_url: str = ""
    idbi_sandbox_api_key: str = ""

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
