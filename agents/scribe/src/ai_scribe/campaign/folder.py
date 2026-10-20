"""Working inside a Campaign Agent running copy.

When the Scribe serves a campaign built with the Campaign Agent, its database
lives in the running copy's `.scribe/` folder and it writes a short summary of
each session to `sessions/`. The Scribe reads the campaign marker directly so it
does not depend on the Campaign Agent's package.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_pc_shared.campaign.models import Entity, PlotThread, SessionRecord, ThreadStatus
from ai_scribe.campaign import writer

MARKER_PATH = Path(".campaign") / "campaign.json"
SCRIBE_DIR = ".scribe"
DATABASE_NAME = "campaign.db"
SESSIONS_DIR = "sessions"
KIND_LABELS = {"npc": "NPC", "location": "location", "faction": "faction"}


def resolve_campaign_folder(folder: Path) -> Path:
    """Return the running copy's absolute path, or raise ValueError explaining why not."""
    folder = folder.expanduser().resolve()
    marker_path = folder / MARKER_PATH
    if not marker_path.is_file():
        raise ValueError(f"{folder} is not a campaign; it has no {MARKER_PATH} marker.")
    try:
        role = json.loads(marker_path.read_text(encoding="utf-8")).get("role")
    except (json.JSONDecodeError, AttributeError) as error:
        raise ValueError(f"The campaign marker in {folder} is not valid.") from error
    if role != "running":
        raise ValueError(
            f"{folder} is a master campaign. The Scribe records games in a running copy; "
            "make one with /start-campaign first."
        )
    return folder


def database_path(folder: Path) -> Path:
    """The Scribe's database inside a running copy, creating `.scribe/` if needed."""
    scribe_dir = resolve_campaign_folder(folder) / SCRIBE_DIR
    scribe_dir.mkdir(exist_ok=True)
    return scribe_dir / DATABASE_NAME


def _local_date(moment: datetime) -> date:
    # SQLite returns naive datetimes; the Scribe always stores UTC.
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone().date()


def _new_summary_path(folder: Path, session_date: date) -> Path:
    sessions = folder / SESSIONS_DIR
    path = sessions / f"{session_date.isoformat()}.md"
    number = 2
    while path.exists():
        path = sessions / f"{session_date.isoformat()}-{number}.md"
        number += 1
    return path


def render_session_summary(
    record: SessionRecord, threads: list[PlotThread], first_met: list[Entity]
) -> str:
    session_date = _local_date(record.started_at).isoformat()
    state = "Final" if record.finalized else "In progress"
    lines = [
        f"# Session {session_date}",
        "",
        f"_{state} summary written by the Scribe. Ask the Scribe for more detail._",
        "",
        record.recap.strip() or "_Nothing has been recorded for this session yet._",
    ]
    if threads:
        lines += ["", "## Plot threads", ""]
        for thread in threads:
            lines.append(f"- **{thread.title}** ({thread.status}): {thread.detail}")
    if first_met:
        lines += ["", "## First met", ""]
        for entity in first_met:
            kind = KIND_LABELS.get(entity.kind, entity.kind)
            lines.append(f"- **{entity.name}** ({kind}): {entity.detail}")
    return "\n".join(lines) + "\n"


def write_session_summary(session: Session, folder: Path, session_id: str) -> Path:
    """Write or rewrite a session's summary in the campaign's `sessions/` folder."""
    folder = resolve_campaign_folder(folder)
    record = session.scalar(select(SessionRecord).where(SessionRecord.session_id == session_id))
    if record is None:
        raise ValueError(f"No session {session_id!r} has been recorded.")

    path = (
        folder / record.summary_file
        if record.summary_file
        else _new_summary_path(folder, _local_date(record.started_at))
    )
    threads = list(
        session.scalars(
            select(PlotThread)
            .where(PlotThread.updated_in == session_id)
            .order_by(PlotThread.title)
        )
    )
    # Open threads first, then the ones closed this session.
    threads.sort(key=lambda thread: thread.status != ThreadStatus.OPEN.value)
    first_met = list(
        session.scalars(
            select(Entity).where(Entity.first_seen_in == session_id).order_by(Entity.name)
        )
    )
    path.parent.mkdir(exist_ok=True)
    path.write_text(render_session_summary(record, threads, first_met), encoding="utf-8")
    record.summary_file = path.relative_to(folder).as_posix()
    session.commit()
    return path


def finalize_session(session: Session, session_id: str, folder: Path | None) -> Path | None:
    """End a session; with a campaign folder, also write its summary there."""
    writer.finalize_session(session, session_id)
    if folder is None:
        return None
    return write_session_summary(session, folder, session_id)
