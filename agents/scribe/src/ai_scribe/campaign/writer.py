"""Write operations on the campaign record.

The Scribe is the campaign database's only writer; consuming agents use the
read-only surface in `ai_pc_shared.campaign.repository`.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_pc_shared.campaign.models import (
    AwarenessKind,
    AwarenessRecord,
    DMNote,
    Entity,
    EntityKind,
    PlotThread,
    SessionRecord,
    ThreadStatus,
    TranscriptLine,
)


def start_session(session: Session, session_id: str) -> SessionRecord:
    """Begin a session, or return the existing one if it is already open."""
    existing = session.scalar(select(SessionRecord).where(SessionRecord.session_id == session_id))
    if existing is not None:
        return existing

    record = SessionRecord(session_id=session_id)
    session.add(record)
    session.commit()
    return record


def append_transcript_line(
    session: Session, session_id: str, speaker: str, text: str
) -> TranscriptLine:
    record = start_session(session, session_id)
    line = TranscriptLine(session_pk=record.id, speaker=speaker, text=text)
    session.add(line)
    session.commit()
    return line


def get_transcript(session: Session, session_id: str) -> list[TranscriptLine]:
    record = session.scalar(select(SessionRecord).where(SessionRecord.session_id == session_id))
    if record is None:
        return []
    stmt = (
        select(TranscriptLine)
        .where(TranscriptLine.session_pk == record.id)
        .order_by(TranscriptLine.spoken_at.asc(), TranscriptLine.id.asc())
    )
    return list(session.scalars(stmt).all())


def update_recap(session: Session, session_id: str, recap: str) -> SessionRecord:
    """Replace the rolling recap. Called repeatedly during a session."""
    record = start_session(session, session_id)
    record.recap = recap
    session.commit()
    return record


def finalize_session(session: Session, session_id: str) -> SessionRecord:
    """End the session and discard its transcript.

    The durable record is the summarized material; the raw speech-to-text is a
    working buffer and does not survive the session that produced it.
    """
    record = start_session(session, session_id)
    record.ended_at = datetime.now(timezone.utc)
    record.finalized = True
    record.transcript_lines = []
    session.commit()
    return record


def upsert_thread(
    session: Session,
    title: str,
    detail: str,
    session_id: str,
    status: ThreadStatus = ThreadStatus.OPEN,
) -> PlotThread:
    thread = session.scalar(select(PlotThread).where(PlotThread.title == title))
    if thread is None:
        thread = PlotThread(title=title, opened_in=session_id)
        session.add(thread)

    thread.detail = detail
    thread.status = status.value
    thread.updated_in = session_id
    session.commit()
    return thread


def close_thread(session: Session, title: str, session_id: str) -> PlotThread | None:
    thread = session.scalar(select(PlotThread).where(PlotThread.title == title))
    if thread is None:
        return None

    thread.status = ThreadStatus.CLOSED.value
    thread.updated_in = session_id
    session.commit()
    return thread


def upsert_entity(
    session: Session,
    name: str,
    kind: EntityKind,
    detail: str,
    session_id: str,
) -> Entity:
    entity = session.scalar(select(Entity).where(Entity.name.ilike(name)))
    if entity is None:
        entity = Entity(name=name, first_seen_in=session_id)
        session.add(entity)

    entity.kind = kind.value
    entity.detail = detail
    entity.last_seen_in = session_id
    session.commit()
    return entity


def record_awareness(
    session: Session,
    session_id: str,
    event: str,
    character: str,
    kind: AwarenessKind,
) -> AwarenessRecord:
    record = AwarenessRecord(
        session_id=session_id, event=event, character=character, kind=kind.value
    )
    session.add(record)
    session.commit()
    return record


def add_dm_note(session: Session, text: str, session_id: str = "") -> DMNote:
    note = DMNote(session_id=session_id, text=text)
    session.add(note)
    session.commit()
    return note


def list_dm_notes(session: Session) -> list[DMNote]:
    """DM-only. Never surfaced through the shared read-only repository."""
    stmt = select(DMNote).order_by(DMNote.created_at.asc())
    return list(session.scalars(stmt).all())
