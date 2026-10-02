import pytest
from sqlalchemy import create_engine

from ai_pc_shared.campaign import repository
from ai_pc_shared.campaign.db import init_campaign_db, make_campaign_session_factory
from ai_pc_shared.campaign.models import AwarenessKind, EntityKind, ThreadStatus
from ai_scribe.campaign import writer


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    init_campaign_db(engine)
    factory = make_campaign_session_factory(engine)
    with factory() as db_session:
        yield db_session


def test_start_session_is_idempotent(session):
    first = writer.start_session(session, "s1")
    second = writer.start_session(session, "s1")
    assert first.id == second.id
    assert len(repository.list_sessions(session)) == 1


def test_transcript_round_trip(session):
    writer.append_transcript_line(session, "s1", "DM", "You enter the tavern.")
    writer.append_transcript_line(session, "s1", "Brennik", "I order an ale.")

    lines = writer.get_transcript(session, "s1")
    assert [(line.speaker, line.text) for line in lines] == [
        ("DM", "You enter the tavern."),
        ("Brennik", "I order an ale."),
    ]


def test_finalize_discards_transcript_but_keeps_recap(session):
    writer.append_transcript_line(session, "s1", "DM", "You enter the tavern.")
    writer.update_recap(session, "s1", "The party reached the tavern.")

    record = writer.finalize_session(session, "s1")

    assert record.finalized is True
    assert record.ended_at is not None
    assert writer.get_transcript(session, "s1") == []
    assert repository.latest_recap(session) == "The party reached the tavern."


def test_upsert_thread_updates_rather_than_duplicates(session):
    writer.upsert_thread(session, "Missing caravan", "A caravan never arrived.", "s1")
    writer.upsert_thread(session, "Missing caravan", "Tracks lead north.", "s2")

    threads = repository.open_threads(session)
    assert len(threads) == 1
    assert threads[0].detail == "Tracks lead north."
    assert threads[0].opened_in == "s1"
    assert threads[0].updated_in == "s2"


def test_closed_threads_are_excluded_from_open_threads(session):
    writer.upsert_thread(session, "Missing caravan", "A caravan never arrived.", "s1")
    writer.close_thread(session, "Missing caravan", "s2")

    assert repository.open_threads(session) == []


def test_upsert_thread_can_close_directly(session):
    writer.upsert_thread(
        session, "Rescue the smith", "Done.", "s1", status=ThreadStatus.CLOSED
    )
    assert repository.open_threads(session) == []


def test_entity_lookup_is_case_insensitive(session):
    writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "A weary knight.", "s1")

    found = repository.find_entity(session, "ser aldric")
    assert found is not None
    assert found.detail == "A weary knight."


def test_entity_upsert_tracks_first_and_last_seen(session):
    writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "A weary knight.", "s1")
    writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "Revealed as a spy.", "s3")

    found = repository.find_entity(session, "Ser Aldric")
    assert found.first_seen_in == "s1"
    assert found.last_seen_in == "s3"
    assert found.detail == "Revealed as a spy."


def test_list_entities_filters_by_kind(session):
    writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "A knight.", "s1")
    writer.upsert_entity(session, "The Gilded Eel", EntityKind.LOCATION, "A tavern.", "s1")

    locations = repository.list_entities(session, EntityKind.LOCATION)
    assert [entity.name for entity in locations] == ["The Gilded Eel"]


def test_who_knows_matches_on_event_substring(session):
    writer.record_awareness(
        session, "s1", "the cultists meet at midnight", "Brennik", AwarenessKind.FIRSTHAND
    )
    writer.record_awareness(
        session, "s1", "the cultists meet at midnight", "Ashra", AwarenessKind.SECONDHAND
    )

    records = repository.who_knows(session, "cultists")
    assert {(r.character, r.kind) for r in records} == {
        ("Brennik", "firsthand"),
        ("Ashra", "secondhand"),
    }


def test_dm_notes_are_not_exposed_through_shared_repository(session):
    writer.add_dm_note(session, "The innkeeper is the villain.", "s1")

    assert len(writer.list_dm_notes(session)) == 1
    assert not hasattr(repository, "list_dm_notes")


def test_all_recaps_skips_sessions_without_one(session):
    writer.update_recap(session, "s1", "First session.")
    writer.start_session(session, "s2")

    assert repository.all_recaps(session) == [("s1", "First session.")]
