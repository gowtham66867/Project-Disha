from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite://"
    seed_file: str = "mock-data/prospects.json"
    data_source: str = "synthetic"
    anthropic_api_key: str = ""
    copilot_model: str = "claude-haiku-4-5-20251001"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
