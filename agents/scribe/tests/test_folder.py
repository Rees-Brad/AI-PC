import json
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from ai_pc_shared.campaign import repository
from ai_pc_shared.campaign.db import init_campaign_db, make_campaign_session_factory
from ai_pc_shared.campaign.models import EntityKind
from ai_scribe.campaign import folder, writer
from ai_scribe.config import database_path, load_settings


def make_campaign(root: Path, role: str = "running") -> Path:
    (root / ".campaign").mkdir(parents=True)
    (root / ".campaign/campaign.json").write_text(
        json.dumps({"role": role, "title": "Crown", "created": "2026-10-01"})
    )
    return root


@pytest.fixture
def running_copy(tmp_path: Path) -> Path:
    return make_campaign(tmp_path / "crown--tuesday")


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    init_campaign_db(engine)
    with make_campaign_session_factory(engine)() as db_session:
        yield db_session


def record_session(session, session_id: str, started: datetime) -> None:
    record = writer.start_session(session, session_id)
    record.started_at = started
    session.commit()
    writer.update_recap(session, session_id, "The party reached Blackmoor.")


def test_database_lives_in_the_running_copy(running_copy: Path) -> None:
    path = folder.database_path(running_copy)
    assert path == running_copy / ".scribe" / "campaign.db"
    assert path.parent.is_dir()


def test_master_and_non_campaign_folders_are_refused(tmp_path: Path) -> None:
    master = make_campaign(tmp_path / "master", role="master")
    with pytest.raises(ValueError, match="is a master campaign.*/start-campaign"):
        folder.database_path(master)
    with pytest.raises(ValueError, match="is not a campaign"):
        folder.database_path(tmp_path)


def test_config_uses_campaign_folder_when_set(
    running_copy: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SCRIBE_CAMPAIGN_FOLDER", raising=False)
    assert database_path(load_settings()) == Path("./campaign.db")
    monkeypatch.setenv("SCRIBE_CAMPAIGN_FOLDER", str(running_copy))
    assert database_path(load_settings()) == running_copy / ".scribe/campaign.db"


def test_env_file_location_can_be_chosen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "scribe.env"
    env_file.write_text("SCRIBE_MODEL=claude-haiku-5-5\nCAMPAIGN_DB_PATH=/tmp/x.db\n")
    monkeypatch.setenv("SCRIBE_ENV_FILE", str(env_file))
    assert load_settings().campaign_db_path == Path("/tmp/x.db")


def test_finalize_writes_a_dated_summary(session, running_copy: Path) -> None:
    record_session(session, "s1", datetime(2026, 10, 20, 18, 0))
    writer.upsert_thread(session, "Missing caravan", "Tracks lead north.", "s1")
    writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "A weary knight.", "s1")
    writer.upsert_entity(session, "Old Friend", EntityKind.NPC, "Met long ago.", "s0")

    path = folder.finalize_session(session, "s1", running_copy)

    assert path is not None and path.parent == running_copy / "sessions"
    assert path.name.startswith("2026-10-2")
    text = path.read_text()
    assert text.startswith("# Session 2026-10-2")
    assert "_Final summary written by the Scribe." in text
    assert "The party reached Blackmoor." in text
    assert "- **Missing caravan** (open): Tracks lead north." in text
    assert "- **Ser Aldric** (NPC): A weary knight." in text
    assert "Old Friend" not in text
    assert repository.get_session_record(session, "s1").summary_file == f"sessions/{path.name}"


def test_second_session_on_same_date_gets_a_suffix(session, running_copy: Path) -> None:
    record_session(session, "s1", datetime(2026, 10, 20, 12, 0))
    record_session(session, "s2", datetime(2026, 10, 20, 12, 30))
    first = folder.finalize_session(session, "s1", running_copy)
    second = folder.finalize_session(session, "s2", running_copy)
    assert first is not None and second is not None
    assert second.name == first.name.replace(".md", "-2.md")


def test_corrected_record_rewrites_the_same_file(session, running_copy: Path) -> None:
    record_session(session, "s1", datetime(2026, 10, 20, 18, 0))
    path = folder.finalize_session(session, "s1", running_copy)
    writer.update_recap(session, "s1", "Corrected: the party reached Greywater.")
    again = folder.write_session_summary(session, running_copy, "s1")
    assert again == path
    assert "Greywater" in again.read_text()
    assert len(list((running_copy / "sessions").glob("*.md"))) == 1


def test_finalize_without_folder_writes_nothing(session) -> None:
    record_session(session, "s1", datetime(2026, 10, 20, 18, 0))
    assert folder.finalize_session(session, "s1", None) is None
    assert repository.get_session_record(session, "s1").finalized is True


def test_summary_for_unknown_session_is_refused(session, running_copy: Path) -> None:
    with pytest.raises(ValueError, match="No session 'nope'"):
        folder.write_session_summary(session, running_copy, "nope")
