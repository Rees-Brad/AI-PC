import asyncio
import json
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from ai_pc_shared.campaign.db import (
    init_campaign_db,
    make_campaign_engine,
    make_campaign_session_factory,
)
from ai_pc_shared.campaign.models import EntityKind
from ai_scribe import mcp_server
from ai_scribe.campaign import folder, writer


@pytest.fixture
def running_copy(tmp_path: Path) -> Path:
    root = tmp_path / "crown--tuesday"
    (root / ".campaign").mkdir(parents=True)
    (root / ".campaign/campaign.json").write_text(
        json.dumps({"role": "running", "title": "Crown", "created": "2026-10-01"})
    )
    engine = make_campaign_engine(folder.database_path(root))
    init_campaign_db(engine)
    with make_campaign_session_factory(engine)() as session:
        writer.update_recap(session, "s1", "The party reached Blackmoor and met Ser Aldric.")
        writer.upsert_thread(session, "Missing caravan", "Tracks lead north.", "s1")
        writer.upsert_entity(session, "Ser Aldric", EntityKind.NPC, "A weary knight.", "s1")
        writer.add_dm_note(session, "Aldric is secretly the caravan thief.", "s1")
    engine.dispose()
    return root


def test_server_registers_query_tools() -> None:
    tools = asyncio.run(mcp_server.server.list_tools())
    assert sorted(tool.name for tool in tools) == [
        "dm_notes",
        "list_sessions",
        "lookup",
        "open_threads",
        "recap",
        "search_record",
        "who_knows",
    ]


def test_tools_answer_from_the_running_copy(running_copy: Path) -> None:
    folder_arg = str(running_copy)
    assert "Blackmoor" in mcp_server.recap(campaign_folder=folder_arg)
    assert "Blackmoor" in mcp_server.recap("s1", campaign_folder=folder_arg)
    assert "A weary knight." in mcp_server.lookup("ser aldric", campaign_folder=folder_arg)
    assert "Missing caravan" in mcp_server.open_threads(campaign_folder=folder_arg)
    assert "s1" in mcp_server.list_sessions(campaign_folder=folder_arg)
    assert "secretly the caravan thief" in mcp_server.dm_notes(campaign_folder=folder_arg)


def test_search_includes_private_notes(running_copy: Path) -> None:
    found = mcp_server.search_record("aldric", campaign_folder=str(running_copy))
    assert "Recap of s1" in found
    assert "Ser Aldric [npc]" in found
    assert "DM note (private): Aldric is secretly the caravan thief." in found


def test_tools_never_write(running_copy: Path) -> None:
    db = running_copy / ".scribe/campaign.db"
    before = db.stat().st_mtime_ns
    mcp_server.search_record("aldric", campaign_folder=str(running_copy))
    assert db.stat().st_mtime_ns == before


def test_missing_record_and_master_are_reported(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    (empty / ".campaign").mkdir(parents=True)
    (empty / ".campaign/campaign.json").write_text(json.dumps({"role": "running"}))
    with pytest.raises(ToolError, match="has not recorded anything"):
        mcp_server.recap(campaign_folder=str(empty))
    (empty / ".campaign/campaign.json").write_text(json.dumps({"role": "master"}))
    with pytest.raises(ToolError, match="is a master campaign"):
        mcp_server.recap(campaign_folder=str(empty))
