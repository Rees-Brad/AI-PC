import argparse

from ai_pc_shared.campaign.db import init_campaign_db, make_campaign_engine
from ai_scribe.config import load_settings


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="ai-scribe", description="AI-backed tabletop RPG campaign scribe"
    )
    parser.parse_args()

    settings = load_settings()
    engine = make_campaign_engine(settings.campaign_db_path)
    init_campaign_db(engine)

    print(f"ai-scribe initialized. Campaign database at {settings.campaign_db_path}")
    print(
        "Discord bot / voice capture not yet implemented. Use "
        "scripts/ingest_transcript.py and scripts/query.py (see README.md)."
    )


if __name__ == "__main__":
    run()
