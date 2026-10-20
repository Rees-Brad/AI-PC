from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from ai_campaign import mcp_server


def test_server_registers_campaign_tools() -> None:
    tools = asyncio.run(mcp_server.server.list_tools())
    assert sorted(tool.name for tool in tools) == [
        "campaign_status",
        "check_campaign",
        "create_campaign",
        "ensure_campaign_docs",
        "extract_pdf_text",
        "snapshot_campaign",
        "start_campaign",
    ]


def test_tools_create_check_and_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    created = mcp_server.create_campaign("crown", "Crown")
    assert created["folder"] == str(tmp_path / "crown")

    status = mcp_server.campaign_status(str(tmp_path / "crown"))
    assert status["marker"]["role"] == "master"

    report = mcp_server.check_campaign("crown")
    assert report["errors"] == 0
    assert report["warnings"] == len(report["issues"]) > 0

    assert mcp_server.ensure_campaign_docs("crown")["created"] == []
    assert mcp_server.snapshot_campaign("crown", "First draft")["method"] == "zip"

    started = mcp_server.start_campaign("crown", "Tuesday")
    assert started["folder"] == str(tmp_path / "crown--tuesday")


def test_refusals_reach_claude_with_their_reason(tmp_path: Path) -> None:
    arguments = {"master_folder": str(tmp_path), "group": "G"}
    with pytest.raises(ToolError, match="no campaign marker"):
        asyncio.run(mcp_server.server.call_tool("start_campaign", arguments))
