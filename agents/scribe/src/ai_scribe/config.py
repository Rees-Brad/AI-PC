import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from ai_scribe.campaign import folder


class Settings(BaseSettings):
    # extra="ignore": an instance directory's .env may carry keys for other
    # tooling; unknown ones should not crash startup.
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    # Summarization is background work and should stay cheap - it must not scale
    # in cost with every spoken turn the way live play does.
    scribe_model: str = "claude-haiku-5-5"

    discord_bot_token: str = ""
    dm_discord_id: str = ""
    scribe_guild_id: str = ""
    scribe_voice_channel_id: str = ""
    scribe_text_channel_id: str = ""

    # A Campaign Agent running copy. When set, the database lives in its
    # .scribe/ folder and session summaries are written to its sessions/ folder.
    scribe_campaign_folder: Path | None = None

    # The campaign record when no campaign folder is set. One database is one
    # campaign.
    campaign_db_path: Path = Path("./campaign.db")


def load_settings(campaign_folder: Path | None = None) -> Settings:
    """Load settings from the environment and SCRIBE_ENV_FILE (default ./.env).

    A campaign folder passed here, such as from a --campaign-folder option,
    overrides SCRIBE_CAMPAIGN_FOLDER.
    """
    env_file = Path(os.environ.get("SCRIBE_ENV_FILE", ".env")).expanduser()
    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]
    if campaign_folder is not None:
        settings.scribe_campaign_folder = campaign_folder
    return settings


def database_path(settings: Settings) -> Path:
    if settings.scribe_campaign_folder is not None:
        return folder.database_path(settings.scribe_campaign_folder)
    return settings.campaign_db_path
