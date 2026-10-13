"""Environment and .env configuration for the Campaign Agent."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = ""
    ai_campaign_model: str = "claude-sonnet-4-5"
    ai_campaign_root: Path = Path("~/ai-pc-campaigns")
    ai_campaign_host: str = "127.0.0.1"
    ai_campaign_port: int = 8765
    ai_campaign_max_context_kb: int = Field(default=500, ge=1, le=10240)


def load_settings() -> Settings:
    env_file = Path(
        os.environ.get("AI_CAMPAIGN_ENV_FILE", "~/ai-pc-campaigns/.env")
    ).expanduser()
    return Settings(_env_file=env_file)