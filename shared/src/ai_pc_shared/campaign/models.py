"""Campaign database schema - the Scribe agent's record of a campaign.

One database is one campaign. The Scribe is its only writer; other agents
open it read-only (see `db.open_campaign_readonly`).
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class CampaignBase(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ThreadStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class EntityKind(str, Enum):
    NPC = "npc"
    LOCATION = "location"
    FACTION = "faction"


class AwarenessKind(str, Enum):
    FIRSTHAND = "firsthand"
    SECONDHAND = "secondhand"


class SessionRecord(CampaignBase):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String, unique=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Rebuilt incrementally during play; finalized when the session ends.
    recap: Mapped[str] = mapped_column(Text, default="")
    finalized: Mapped[bool] = mapped_column(Boolean, default=False)

    transcript_lines: Mapped[list["TranscriptLine"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class TranscriptLine(CampaignBase):
    """Raw speech-to-text. A working buffer only - purged when the recap is finalized."""

    __tablename__ = "transcript_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_pk: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    speaker: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    spoken_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    session: Mapped["SessionRecord"] = relationship(back_populates="transcript_lines")


class PlotThread(CampaignBase):
    __tablename__ = "plot_threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String, default=ThreadStatus.OPEN.value)
    opened_in: Mapped[str] = mapped_column(String, default="")
    updated_in: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Entity(CampaignBase):
    """An NPC, location, or faction the party has encountered."""

    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[str] = mapped_column(String, default=EntityKind.NPC.value)
    detail: Mapped[str] = mapped_column(Text, default="")
    first_seen_in: Mapped[str] = mapped_column(String, default="")
    last_seen_in: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class AwarenessRecord(CampaignBase):
    """Who knows about an event, and how they learned it.

    Inferred during summarization, while the transcript still exists - it cannot be
    recovered afterwards, so it is stored rather than derived at query time.
    """

    __tablename__ = "awareness"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String)
    event: Mapped[str] = mapped_column(Text)
    character: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String, default=AwarenessKind.FIRSTHAND.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DMNote(CampaignBase):
    """DM-private material. Never exposed to other agents through the campaign DB."""

    __tablename__ = "dm_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String, default="")
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
