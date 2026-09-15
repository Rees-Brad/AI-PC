import argparse

from ai_pc.config import load_settings
from ai_pc.persistence.db import init_db, make_engine


def run() -> None:
    parser = argparse.ArgumentParser(prog="ai-pc", description="AI-backed D&D 5e Player Character")
    parser.parse_args()

    settings = load_settings()
    engine = make_engine(settings.ai_pc_db_path)
    init_db(engine)

    print(f"ai-pc initialized. Database at {settings.ai_pc_db_path}")
    print("Discord bot / gameplay loop not yet implemented (see REQUIREMENTS.md, plan Phase 1+).")


if __name__ == "__main__":
    run()
