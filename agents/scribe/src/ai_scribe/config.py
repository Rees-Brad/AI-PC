from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": an instance directory's .env may carry keys for other
    # tooling; unknown ones should not crash startup.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: str = ""
    # Summarization is background work and should stay cheap - it must not scale
    # in cost with every spoken turn the way live play does.
    scribe_model: str = "claude-haiku-4-5"

    discord_bot_token: str = ""
    dm_discord_id: str = ""
    scribe_guild_id: str = ""
    scribe_voice_channel_id: str = ""
    scribe_text_channel_id: str = ""

    # The campaign record this Scribe owns. One database is one campaign.
    campaign_db_path: Path = Path("./campaign.db")


def load_settings() -> Settings:
    return Settings()
