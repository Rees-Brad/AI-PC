from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ai_pc_shared.campaign.models import CampaignBase


def make_campaign_engine(db_path: Path) -> Engine:
    """Read/write engine. Only the Scribe agent should use this."""
    return create_engine(f"sqlite:///{db_path}")


def open_campaign_readonly(db_path: Path) -> Engine:
    """Read-only engine for consuming agents (PC, and later DM/NPC).

    SQLite enforces this at the connection level, so a consumer that tries to
    write gets an error rather than silently corrupting the campaign record.
    """
    return create_engine(f"sqlite:///file:{db_path}?mode=ro&uri=true")


def init_campaign_db(engine: Engine) -> None:
    CampaignBase.metadata.create_all(engine)


def make_campaign_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
