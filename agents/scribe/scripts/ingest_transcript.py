"""Feed a transcript file to the Scribe and update the campaign record.

Lets the summarization path be exercised without Discord or speech-to-text.

Usage:
    python scripts/ingest_transcript.py <session-id> <transcript-file> [--finalize]
        [--campaign-folder <running copy>]

With a campaign folder (or SCRIBE_CAMPAIGN_FOLDER), the record lives in that running
copy's .scribe/ folder, and --finalize also writes the session's summary to its
sessions/ folder.

The transcript file is one line per utterance, "Speaker: what they said".
Blank lines and lines starting with # are ignored.
"""

import argparse
from pathlib import Path

from ai_pc_shared.campaign.db import (
    init_campaign_db,
    make_campaign_engine,
    make_campaign_session_factory,
)
from ai_pc_shared.llm.client import make_client
from ai_scribe.campaign import folder, writer
from ai_scribe.config import database_path, load_settings
from ai_scribe.llm.summarize import ingest


def parse_transcript(text: str) -> list[tuple[str, str]]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        speaker, separator, said = line.partition(":")
        if not separator:
            raise ValueError(f"Malformed transcript line (expected 'Speaker: text'): {raw!r}")
        lines.append((speaker.strip(), said.strip()))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_id")
    parser.add_argument("transcript", type=Path)
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="End the session and discard its transcript buffer afterwards",
    )
    parser.add_argument(
        "--campaign-folder",
        type=Path,
        help="A Campaign Agent running copy to keep the record in",
    )
    args = parser.parse_args()

    utterances = parse_transcript(args.transcript.read_text())
    if not utterances:
        print(f"No usable lines in {args.transcript}")
        return

    settings = load_settings(args.campaign_folder)
    engine = make_campaign_engine(database_path(settings))
    init_campaign_db(engine)
    session_factory = make_campaign_session_factory(engine)

    with session_factory() as session:
        for speaker, said in utterances:
            writer.append_transcript_line(session, args.session_id, speaker, said)
        print(f"Buffered {len(utterances)} lines for session {args.session_id!r}. Summarizing...")

        client = make_client(settings.anthropic_api_key)
        digest = ingest(client, settings, session, args.session_id)

        summary_path = None
        if args.finalize:
            summary_path = folder.finalize_session(
                session, args.session_id, settings.scribe_campaign_folder
            )

    print(f"\n=== Recap ===\n{digest.recap}")

    if digest.threads:
        print("\n=== Threads ===")
        for thread in digest.threads:
            state = "closed" if thread.closed else "open"
            print(f"- [{state}] {thread.title}: {thread.detail}")

    if digest.entities:
        print("\n=== Entities ===")
        for entity in digest.entities:
            print(f"- {entity.name} [{entity.kind.value}]: {entity.detail}")

    if digest.awareness:
        print("\n=== Awareness ===")
        for entry in digest.awareness:
            kind = "secondhand" if entry.secondhand else "firsthand"
            print(f"- {entry.character} knows {kind}: {entry.event}")

    if args.finalize:
        print(f"\nSession {args.session_id!r} finalized; transcript buffer discarded.")
        if summary_path is not None:
            print(f"Session summary written to {summary_path}")


if __name__ == "__main__":
    main()
