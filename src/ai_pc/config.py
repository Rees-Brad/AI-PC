from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str = ""
    ai_pc_model: str = "claude-sonnet-5"
    ai_pc_summary_model: str = "claude-haiku-4-5"

    discord_bot_token: str = ""
    dm_discord_id: str = ""
    owner_discord_id: str = ""

    ai_pc_db_path: Path = Path("./ai_pc.db")


def load_settings() -> Settings:
    return Settings()
