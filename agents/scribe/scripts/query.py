"""Ask the campaign record a question - the CLI equivalent of the Scribe's slash commands.

Usage:
    python scripts/query.py recap
    python scripts/query.py who "Brennik Stonejaw"
    python scripts/query.py where "The Gilded Eel"
    python scripts/query.py threads
    python scripts/query.py knows "the cultists' meeting"
    python scripts/query.py sessions
    python scripts/query.py notes
    python scripts/query.py search "ledger"

Add --campaign-folder <running copy> to read the record kept in a Campaign Agent
running copy. `notes` and `search` include the DM's private notes.
"""

import argparse
from pathlib import Path

from ai_pc_shared.campaign.db import make_campaign_session_factory, open_campaign_readonly
from ai_scribe.config import database_path, load_settings
from ai_scribe.llm import queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-folder", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("recap", "threads", "sessions", "notes"):
        subparsers.add_parser(name)
    for name in ("who", "where", "knows", "search"):
        sub = subparsers.add_parser(name)
        sub.add_argument("query")

    args = parser.parse_args()

    db_path = database_path(load_settings(args.campaign_folder))
    if not db_path.exists():
        print(f"No campaign database at {db_path}. Ingest a transcript first.")
        return

    # Queries never write, so open the same read-only way consuming agents do.
    engine = open_campaign_readonly(db_path)
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
        elif args.command == "sessions":
            print(queries.sessions(session))
        elif args.command == "notes":
            print(queries.dm_notes(session))
        elif args.command == "search":
            print(queries.search(session, args.query))


if __name__ == "__main__":
    main()
