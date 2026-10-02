"""Answering the table's history questions.

These are structured lookups against the campaign record, not LLM calls -
awareness was already inferred at ingest time, while the transcript still
existed. Formatting is kept pure so it can be tested directly.
"""

from sqlalchemy.orm import Session

from ai_pc_shared.campaign import repository
from ai_pc_shared.campaign.models import AwarenessKind, AwarenessRecord, Entity, PlotThread


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
