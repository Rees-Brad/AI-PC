import argparse
from pathlib import Path

from ai_pc_shared.campaign.db import init_campaign_db, make_campaign_engine
from ai_scribe.config import database_path, load_settings


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="ai-scribe", description="AI-backed tabletop RPG campaign scribe"
    )
    parser.add_argument(
        "--campaign-folder",
        type=Path,
        help="A Campaign Agent running copy to keep the record in",
    )
    args = parser.parse_args()

    try:
        db_path = database_path(load_settings(args.campaign_folder))
    except ValueError as error:
        parser.exit(1, f"ai-scribe: {error}\n")
    init_campaign_db(make_campaign_engine(db_path))

    print(f"ai-scribe initialized. Campaign database at {db_path}")
    print(
        "Discord bot / voice capture not yet implemented. Use "
        "scripts/ingest_transcript.py and scripts/query.py (see README.md)."
    )


if __name__ == "__main__":
    run()
