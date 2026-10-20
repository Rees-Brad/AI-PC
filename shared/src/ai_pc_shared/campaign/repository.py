"""Read-only access to the campaign record.

This is the surface consuming agents (PC, later DM/NPC) use. Writes live in the
Scribe agent, which owns the database.

DM-private notes are deliberately absent: they are visible only to the DM and
are never exposed to other agents (see the Scribe's Access control requirement).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_pc_shared.campaign.models import (
    AwarenessRecord,
    Entity,
    EntityKind,
    PlotThread,
    SessionRecord,
    ThreadStatus,
)


def get_session_record(session: Session, session_id: str) -> SessionRecord | None:
    return session.scalar(select(SessionRecord).where(SessionRecord.session_id == session_id))


def list_sessions(session: Session) -> list[SessionRecord]:
    stmt = select(SessionRecord).order_by(SessionRecord.started_at.asc())
    return list(session.scalars(stmt).all())


def latest_recap(session: Session) -> str | None:
    """The most recent session's recap, finalized or not."""
    stmt = select(SessionRecord).order_by(SessionRecord.started_at.desc()).limit(1)
    record = session.scalar(stmt)
    if record is None or not record.recap:
        return None
    return record.recap


def all_recaps(session: Session) -> list[tuple[str, str]]:
    """(session_id, recap) oldest first - the long-term memory a PC agent loads."""
    return [(r.session_id, r.recap) for r in list_sessions(session) if r.recap]


def find_entity(session: Session, name: str) -> Entity | None:
    """Case-insensitive lookup by name."""
    stmt = select(Entity).where(Entity.name.ilike(name))
    return session.scalar(stmt)


def list_entities(session: Session, kind: EntityKind | None = None) -> list[Entity]:
    stmt = select(Entity)
    if kind is not None:
        stmt = stmt.where(Entity.kind == kind.value)
    return list(session.scalars(stmt.order_by(Entity.name.asc())).all())


def list_threads(session: Session) -> list[PlotThread]:
    """Every plot thread, open or closed, most recently updated first."""
    return list(session.scalars(select(PlotThread).order_by(PlotThread.updated_at.desc())).all())


def open_threads(session: Session) -> list[PlotThread]:
    stmt = (
        select(PlotThread)
        .where(PlotThread.status == ThreadStatus.OPEN.value)
        .order_by(PlotThread.updated_at.desc())
    )
    return list(session.scalars(stmt).all())


def who_knows(session: Session, event_query: str) -> list[AwarenessRecord]:
    """Characters aware of events matching `event_query`, and how they learned it."""
    stmt = select(AwarenessRecord).where(AwarenessRecord.event.ilike(f"%{event_query}%"))
    return list(session.scalars(stmt).all())


def awareness_for_character(session: Session, character: str) -> list[AwarenessRecord]:
    stmt = (
        select(AwarenessRecord)
        .where(AwarenessRecord.character.ilike(character))
        .order_by(AwarenessRecord.created_at.asc())
    )
    return list(session.scalars(stmt).all())
