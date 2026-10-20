"""Answering the table's history questions.

These are structured lookups against the campaign record, not LLM calls -
awareness was already inferred at ingest time, while the transcript still
existed. Formatting is kept pure so it can be tested directly.
"""

from sqlalchemy.orm import Session

from ai_pc_shared.campaign import repository
from ai_pc_shared.campaign.models import AwarenessKind, AwarenessRecord, Entity, PlotThread
from ai_scribe.campaign import writer


def format_entity(entity: Entity) -> str:
    seen = entity.last_seen_in or entity.first_seen_in
    suffix = f" (last seen: {seen})" if seen else ""
    return f"{entity.name} [{entity.kind}]{suffix}\n{entity.detail}".strip()


def format_threads(threads: list[PlotThread]) -> str:
    if not threads:
        return "No open threads."
    return "\n".join(f"- {thread.title}: {thread.detail}" for thread in threads)


def format_awareness(records: list[AwarenessRecord]) -> str:
    if not records:
        return "No record of anyone being aware of that."

    by_character: dict[str, str] = {}
    for record in records:
        # Firsthand knowledge outranks secondhand if a character has both.
        if by_character.get(record.character) == AwarenessKind.FIRSTHAND.value:
            continue
        by_character[record.character] = record.kind

    return "\n".join(
        f"- {character}: {kind}" for character, kind in sorted(by_character.items())
    )


def recap(session: Session) -> str:
    latest = repository.latest_recap(session)
    return latest or "No sessions recorded yet."


def lookup(session: Session, name: str) -> str:
    entity = repository.find_entity(session, name)
    if entity is None:
        return f"Nothing recorded about {name!r}."
    return format_entity(entity)


def threads(session: Session) -> str:
    return format_threads(repository.open_threads(session))


def knows(session: Session, event_query: str) -> str:
    return format_awareness(repository.who_knows(session, event_query))


# Private DM queries. These include DM-private records, so they are only for
# answers that go to the DM alone (see the Scribe's Access control requirement).


def session_recap(session: Session, session_id: str) -> str:
    record = repository.get_session_record(session, session_id)
    if record is None:
        return f"No session {session_id!r} has been recorded."
    return record.recap or f"Session {session_id!r} has no recap yet."


def sessions(session: Session) -> str:
    records = repository.list_sessions(session)
    if not records:
        return "No sessions recorded yet."
    lines = []
    for record in records:
        state = "final" if record.finalized else "in progress"
        summary = f", summary: {record.summary_file}" if record.summary_file else ""
        lines.append(f"- {record.session_id} ({record.started_at:%Y-%m-%d}, {state}{summary})")
    return "\n".join(lines)


def dm_notes(session: Session) -> str:
    notes = writer.list_dm_notes(session)
    if not notes:
        return "No DM notes recorded."
    return "\n".join(
        f"- [{note.session_id or 'no session'}] {note.text}" for note in notes
    )


def search(session: Session, text: str) -> str:
    """Every part of the record that mentions `text`, including DM notes."""
    needle = text.casefold()
    found = []
    for record in repository.list_sessions(session):
        if needle in record.recap.casefold():
            found.append(f"Recap of {record.session_id}: {record.recap}")
    for thread in repository.list_threads(session):
        if needle in f"{thread.title} {thread.detail}".casefold():
            found.append(f"Thread ({thread.status}): {thread.title}: {thread.detail}")
    for entity in repository.list_entities(session):
        if needle in f"{entity.name} {entity.detail}".casefold():
            found.append(format_entity(entity))
    for aware in repository.who_knows(session, text):
        found.append(f"Awareness: {aware.character} knows {aware.kind}: {aware.event}")
    for note in writer.list_dm_notes(session):
        if needle in note.text.casefold():
            found.append(f"DM note (private): {note.text}")
    return "\n\n".join(found) if found else f"Nothing in the record mentions {text!r}."
