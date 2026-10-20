import pytest
from sqlalchemy import create_engine

from ai_pc_shared.campaign import repository
from ai_pc_shared.campaign.db import init_campaign_db, make_campaign_session_factory
from ai_pc_shared.campaign.models import EntityKind
from ai_scribe.campaign import writer
from ai_scribe.llm import queries
from ai_scribe.llm.summarize import (
    AwarenessEntry,
    EntityUpdate,
    SessionDigest,
    ThreadUpdate,
    apply_digest,
    build_prompt,
    format_transcript,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    init_campaign_db(engine)
    factory = make_campaign_session_factory(engine)
    with factory() as db_session:
        yield db_session


def _digest(**overrides) -> SessionDigest:
    defaults = dict(
        recap="The party reached Blackmoor and met Ser Aldric.",
        threads=[ThreadUpdate(title="Missing caravan", detail="Tracks lead north.")],
        entities=[
            EntityUpdate(name="Ser Aldric", kind=EntityKind.NPC, detail="A weary knight."),
            EntityUpdate(name="Blackmoor", kind=EntityKind.LOCATION, detail="A border town."),
        ],
        awareness=[
            AwarenessEntry(event="Ser Aldric's warning", character="Brennik"),
            AwarenessEntry(event="Ser Aldric's warning", character="Ashra", secondhand=True),
        ],
    )
    defaults.update(overrides)
    return SessionDigest(**defaults)


def test_format_transcript_uses_speaker_prefixes(session):
    writer.append_transcript_line(session, "s1", "DM", "You enter the tavern.")
    writer.append_transcript_line(session, "s1", "Brennik", "I order an ale.")

    formatted = format_transcript(writer.get_transcript(session, "s1"))
    assert formatted == "DM: You enter the tavern.\nBrennik: I order an ale."


def test_build_prompt_asks_for_an_update_when_a_recap_exists():
    prompt = build_prompt("Earlier, the party left Westhook.", "DM: You arrive at Blackmoor.")
    assert "Earlier, the party left Westhook." in prompt
    assert "rather than starting over" in prompt


def test_build_prompt_handles_a_fresh_session():
    prompt = build_prompt("", "DM: You arrive at Blackmoor.")
    assert "no recap yet" in prompt


def test_apply_digest_writes_every_record_type(session):
    apply_digest(session, "s1", _digest())

    assert repository.latest_recap(session).startswith("The party reached Blackmoor")
    assert [t.title for t in repository.open_threads(session)] == ["Missing caravan"]
    assert repository.find_entity(session, "Blackmoor").kind == EntityKind.LOCATION.value
    assert len(repository.who_knows(session, "warning")) == 2


def test_apply_digest_is_incremental_across_calls(session):
    apply_digest(session, "s1", _digest())
    apply_digest(
        session,
        "s2",
        _digest(
            recap="Later, the caravan was found.",
            threads=[ThreadUpdate(title="Missing caravan", detail="Found, looted.", closed=True)],
            entities=[],
            awareness=[],
        ),
    )

    # The thread was updated in place and closed, not duplicated.
    assert repository.open_threads(session) == []
    assert repository.latest_recap(session) == "Later, the caravan was found."
    assert len(repository.list_sessions(session)) == 2


def test_firsthand_outranks_secondhand_in_awareness_output(session):
    apply_digest(
        session,
        "s1",
        _digest(
            awareness=[
                AwarenessEntry(event="the ambush", character="Brennik", secondhand=True),
                AwarenessEntry(event="the ambush", character="Brennik"),
            ]
        ),
    )

    assert queries.knows(session, "ambush") == "- Brennik: firsthand"


def test_knows_reports_nothing_for_an_unknown_event(session):
    assert "No record" in queries.knows(session, "the dragon")


def test_lookup_reports_nothing_for_an_unknown_entity(session):
    assert "Nothing recorded" in queries.lookup(session, "Nobody")


def test_threads_output_lists_open_threads(session):
    apply_digest(session, "s1", _digest())
    assert queries.threads(session) == "- Missing caravan: Tracks lead north."


class _StubMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = {}

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def _stub_client(response):
    from types import SimpleNamespace

    return SimpleNamespace(messages=_StubMessages(response))


def test_summarize_reports_refusals_clearly():
    from types import SimpleNamespace

    from ai_scribe.config import Settings
    from ai_scribe.llm.summarize import summarize_session

    response = SimpleNamespace(
        stop_reason="refusal",
        stop_details=SimpleNamespace(category="general_harms"),
        parsed_output=None,
    )
    with pytest.raises(RuntimeError, match="declined.*general_harms"):
        summarize_session(_stub_client(response), Settings(), "", [])


def test_summarize_uses_configured_model_and_room_for_thinking():
    from types import SimpleNamespace

    from ai_scribe.config import Settings
    from ai_scribe.llm.summarize import summarize_session

    digest = _digest()
    client = _stub_client(SimpleNamespace(stop_reason="end_turn", parsed_output=digest))
    assert summarize_session(client, Settings(), "", []) is digest
    assert client.messages.kwargs["model"] == "claude-haiku-5-5"
    assert client.messages.kwargs["max_tokens"] == 16000
