"""Turn a session transcript into the campaign's durable record.

The LLM call and the database merge are kept separate: `summarize_session` does
the former, `apply_digest` the latter. The merge is pure bookkeeping and is
covered by tests without touching the API.
"""

import anthropic
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_pc_shared.campaign.models import AwarenessKind, EntityKind, ThreadStatus, TranscriptLine
from ai_scribe.campaign import writer
from ai_scribe.config import Settings


class ThreadUpdate(BaseModel):
    title: str = Field(description="Short stable name for the thread; reuse it across sessions")
    detail: str = Field(description="Current state of the thread in a sentence or two")
    closed: bool = Field(default=False, description="True if resolved this session")


class EntityUpdate(BaseModel):
    name: str
    kind: EntityKind
    detail: str = Field(description="What the party currently knows about this entity")


class AwarenessEntry(BaseModel):
    event: str = Field(description="Short description of the event")
    character: str = Field(description="Character who is aware of it")
    secondhand: bool = Field(
        default=False, description="True if they were told rather than present"
    )


class SessionDigest(BaseModel):
    recap: str = Field(
        description=(
            "Brief narrative summary of the session so far: what the party did, what "
            "changed, and what was decided, in a few short paragraphs"
        )
    )
    threads: list[ThreadUpdate] = Field(default_factory=list)
    entities: list[EntityUpdate] = Field(default_factory=list)
    awareness: list[AwarenessEntry] = Field(default_factory=list)


SYSTEM_PROMPT = (
    "You are the Scribe for a tabletop RPG campaign. You keep the campaign's "
    "record: what happened, what is unresolved, who and what the party has "
    "encountered, and who is aware of what.\n\n"
    "Rules you follow strictly:\n"
    "- Record what actually happened. Where something was ambiguous or "
    "inaudible, say so rather than inventing a plausible version of it.\n"
    "- You are an observer, not a participant. Do not editorialize, offer "
    "advice, or narrate events that did not occur.\n"
    "- Reuse existing thread titles and entity names when updating them, so the "
    "record stays consolidated rather than duplicated.\n"
    "- Keep the recap brief. It is saved as the session's summary for the DM; "
    "fuller detail stays in the threads, entities, and awareness records.\n\n"
    "Awareness rules:\n"
    "- A character is aware FIRSTHAND of events they were present for.\n"
    "- When a split party regroups, assume they caught each other up: absent "
    "characters become aware SECONDHAND of material information (what was "
    "found, who was met, what was decided).\n"
    "- Incidental colour and private character moments do not transfer.\n"
    "- Concealment is sticky. Anything a character deliberately hid from the "
    "party does NOT transfer on regrouping, no matter how much time passes. It "
    "stays known only to them until they actually share it on screen."
)


def format_transcript(lines: list[TranscriptLine]) -> str:
    return "\n".join(f"{line.speaker}: {line.text}" for line in lines)


def build_prompt(prior_recap: str, transcript: str) -> str:
    sections = []
    if prior_recap:
        sections.append(
            "Here is the recap of this session so far. Update it to incorporate "
            "the new material below, rather than starting over:\n\n" + prior_recap
        )
    else:
        sections.append("This is the start of a new session; there is no recap yet.")

    sections.append("New transcript material:\n\n" + transcript)
    sections.append(
        "Produce the updated recap, the current state of any plot threads, any "
        "NPCs/locations/factions involved, and who is aware of what happened."
    )
    return "\n\n---\n\n".join(sections)


def apply_digest(session: Session, session_id: str, digest: SessionDigest) -> None:
    """Merge a digest into the campaign record. Pure bookkeeping, no API calls."""
    writer.update_recap(session, session_id, digest.recap)

    for thread in digest.threads:
        writer.upsert_thread(
            session,
            title=thread.title,
            detail=thread.detail,
            session_id=session_id,
            status=ThreadStatus.CLOSED if thread.closed else ThreadStatus.OPEN,
        )

    for entity in digest.entities:
        writer.upsert_entity(
            session,
            name=entity.name,
            kind=entity.kind,
            detail=entity.detail,
            session_id=session_id,
        )

    for entry in digest.awareness:
        writer.record_awareness(
            session,
            session_id=session_id,
            event=entry.event,
            character=entry.character,
            kind=AwarenessKind.SECONDHAND if entry.secondhand else AwarenessKind.FIRSTHAND,
        )


def summarize_session(
    client: anthropic.Anthropic,
    settings: Settings,
    prior_recap: str,
    lines: list[TranscriptLine],
) -> SessionDigest:
    response = client.messages.parse(
        model=settings.scribe_model,
        # Room for the model's thinking as well as the digest itself.
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(prior_recap, format_transcript(lines))}],
        output_format=SessionDigest,
    )
    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        raise RuntimeError(f"Claude declined to summarize this material (category={category!r})")
    if response.parsed_output is None:
        raise RuntimeError(
            f"Claude did not return a structured digest (stop_reason={response.stop_reason!r})"
        )
    return response.parsed_output


def ingest(
    client: anthropic.Anthropic,
    settings: Settings,
    session: Session,
    session_id: str,
) -> SessionDigest:
    """Summarize the current transcript buffer and merge the result."""
    record = writer.start_session(session, session_id)
    lines = writer.get_transcript(session, session_id)
    if not lines:
        raise RuntimeError(f"No transcript recorded for session {session_id!r}")

    digest = summarize_session(client, settings, record.recap, lines)
    apply_digest(session, session_id, digest)
    return digest
