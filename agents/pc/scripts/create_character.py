"""Create a new AI-driven D&D 5e character and save it to the database.

Usage:
    python scripts/create_character.py [--class CLASS] [--alignment ALIGNMENT]
        [--race RACE [RACE ...]] [--gender GENDER [GENDER ...]]
        [--level LEVEL] [--name NAME]

Anything not passed is left to the AI, per REQUIREMENTS.md (Character
Creation, path 1).
"""

import argparse

from ai_pc.character.creation import CreationConstraints, create_character
from ai_pc.config import load_settings
from ai_pc.llm.prompts import sheet_summary
from ai_pc_shared.llm.client import make_client
from ai_pc_shared.persistence.db import init_db, make_engine, make_session_factory
from ai_pc_shared.persistence.repository import save_character_sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class", dest="class_suggestion", default=None)
    parser.add_argument("--alignment", default=None)
    parser.add_argument("--race", nargs="+", default=None, dest="allowed_races")
    parser.add_argument("--gender", nargs="+", default=None, dest="allowed_genders")
    parser.add_argument("--level", type=int, default=1, dest="starting_level")
    parser.add_argument("--name", default=None, dest="name_override")
    args = parser.parse_args()

    constraints = CreationConstraints(
        class_suggestion=args.class_suggestion,
        alignment=args.alignment,
        allowed_races=args.allowed_races,
        allowed_genders=args.allowed_genders,
        starting_level=args.starting_level,
        name_override=args.name_override,
    )

    settings = load_settings()
    client = make_client(settings.anthropic_api_key)

    print("Creating character...")
    sheet = create_character(client, settings, constraints)

    engine = make_engine(settings.ai_pc_db_path)
    init_db(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        save_character_sheet(session, sheet)

    print(f"\nSaved '{sheet.name}' to {settings.ai_pc_db_path}\n")
    print(sheet_summary(sheet))
    print(f"\nPersona: {sheet.persona}")
    print(f"Background: {sheet.background}")


if __name__ == "__main__":
    main()
