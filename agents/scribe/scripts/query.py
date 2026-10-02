"""Ask the campaign record a question - the CLI equivalent of the Scribe's slash commands.

Usage:
    python scripts/query.py recap
    python scripts/query.py who "Brennik Stonejaw"
    python scripts/query.py where "The Gilded Eel"
    python scripts/query.py threads
    python scripts/query.py knows "the cultists' meeting"
"""

import argparse

from ai_pc_shared.campaign.db import make_campaign_session_factory, open_campaign_readonly
from ai_scribe.config import load_settings
from ai_scribe.llm import queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("recap")
    subparsers.add_parser("threads")
    for name in ("who", "where", "knows"):
        sub = subparsers.add_parser(name)
        sub.add_argument("query")

    args = parser.parse_args()

    settings = load_settings()
    if not settings.campaign_db_path.exists():
        print(f"No campaign database at {settings.campaign_db_path}. Ingest a transcript first.")
        return

    # Queries never write, so open the same read-only way consuming agents do.
    engine = open_campaign_readonly(settings.campaign_db_path)
    session_factory = make_campaign_session_factory(engine)

    with session_factory() as session:
        if args.command == "recap":
            print(queries.recap(session))
        elif args.command == "threads":
            print(queries.threads(session))
        elif args.command in ("who", "where"):
            print(queries.lookup(session, args.query))
        elif args.command == "knows":
            print(queries.knows(session, args.query))


if __name__ == "__main__":
    main()
