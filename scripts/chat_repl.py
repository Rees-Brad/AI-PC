"""Text-only interaction loop with a saved AI PC - no Discord, no voice.

Usage:
    python scripts/chat_repl.py <character-name>

Type lines as the DM/table would speak them; type "quit" to exit.
"""

import argparse
import uuid

from ai_pc.config import load_settings
from ai_pc.llm.client import make_client
from ai_pc.llm.prompts import build_system_prompt
from ai_pc.llm.tools import build_tools
from ai_pc.persistence.db import init_db, make_engine, make_session_factory
from ai_pc.persistence.repository import append_session_log, get_character_row, load_character_sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character_name")
    args = parser.parse_args()

    settings = load_settings()
    engine = make_engine(settings.ai_pc_db_path)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        sheet = load_character_sheet(session, args.character_name)
        if sheet is None:
            print(f"No character named '{args.character_name}'. Run create_character.py first.")
            return
        character_id = get_character_row(session, args.character_name).id

    client = make_client(settings)
    tools = build_tools(args.character_name, session_factory)
    session_id = str(uuid.uuid4())[:8]

    print(f"Chatting with {sheet.name} ({sheet.character_class} {sheet.level}). Type 'quit' to exit.\n")

    messages: list = []
    while True:
        try:
            user_input = input("DM> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue

        with session_factory() as log_session:
            append_session_log(
                log_session, character_id, session_id, "user", {"text": user_input}
            )

        messages.append({"role": "user", "content": user_input})

        with session_factory() as sheet_session:
            current_sheet = load_character_sheet(sheet_session, args.character_name)
        system_prompt = build_system_prompt(current_sheet)

        runner = client.beta.messages.tool_runner(
            model=settings.ai_pc_model,
            max_tokens=2000,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        final_text = ""
        last_message = None
        for message in runner:
            last_message = message
            for block in message.content:
                if block.type == "text":
                    final_text = block.text

        if last_message is not None:
            messages.append({"role": "assistant", "content": last_message.content})

        print(f"\n{sheet.name}> {final_text}\n")

        with session_factory() as log_session:
            append_session_log(
                log_session, character_id, session_id, "assistant", {"text": final_text}
            )


if __name__ == "__main__":
    main()
