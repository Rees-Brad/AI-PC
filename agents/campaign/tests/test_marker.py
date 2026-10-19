from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_campaign.marker import MARKER_PATH, CampaignMarker, read_marker, write_marker


def test_missing_marker_reads_as_none(tmp_path: Path) -> None:
    assert read_marker(tmp_path) is None


def test_marker_round_trips_and_keeps_unknown_keys(tmp_path: Path) -> None:
    (tmp_path / MARKER_PATH).parent.mkdir()
    (tmp_path / MARKER_PATH).write_text(
        json.dumps(
            {"role": "master", "title": "T", "created": "2026-10-19", "discord_channel": "x"}
        )
    )
    marker = read_marker(tmp_path)
    assert marker is not None
    assert marker.extra == {"discord_channel": "x"}

    marker.edition = "2"
    write_marker(tmp_path, marker)
    data = json.loads((tmp_path / MARKER_PATH).read_text())
    assert data["discord_channel"] == "x"
    assert data["edition"] == "2"
    assert "source_master" not in data


@pytest.mark.parametrize(
    "content, message",
    [
        ("not json", "not valid JSON"),
        ("[]", "must be a JSON object"),
        ('{"role": "draft", "title": "T", "created": "d"}', "role"),
        ('{"role": "master"}', "title and created"),
    ],
)
def test_invalid_markers_are_rejected(tmp_path: Path, content: str, message: str) -> None:
    (tmp_path / MARKER_PATH).parent.mkdir()
    (tmp_path / MARKER_PATH).write_text(content)
    with pytest.raises(ValueError, match=message):
        read_marker(tmp_path)


def test_write_marker_creates_folder(tmp_path: Path) -> None:
    write_marker(tmp_path, CampaignMarker(role="running", title="T", created="d"))
    assert read_marker(tmp_path) == CampaignMarker(role="running", title="T", created="d")
