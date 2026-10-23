from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_campaign.lifecycle import (
    SRD_5_1_ATTRIBUTION,
    SRD_5_2_ATTRIBUTION,
    create_campaign,
    ensure_campaign_docs,
    slugify,
    snapshot_campaign,
    srd_attribution,
    start_campaign,
)
from ai_campaign.marker import read_marker


def git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=folder, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_create_campaign_scaffolds_a_master(tmp_path: Path) -> None:
    result = create_campaign(tmp_path / "crown", "  The Sunken\nCrown ")
    root = tmp_path / "crown"
    assert result["created"] == [
        ".campaign/campaign.json",
        ".gitignore",
        "GETTING_STARTED.md",
        "OPEN_ITEMS.md",
        "WORKLOG.md",
        "campaign.md",
        "chapters/.gitkeep",
        "items.md",
        "locations.md",
        "maps/.gitkeep",
        "npcs.md",
    ]
    assert result["rules"] == "D&D 5e (2024)"
    assert (root / "campaign.md").read_text().startswith("# The Sunken Crown\n")
    assert "[Key NPCs](npcs.md)" in (root / "campaign.md").read_text()
    assert "Add one entry per key NPC." in (root / "npcs.md").read_text()
    assert ".env" in (root / ".gitignore").read_text()
    marker = read_marker(root)
    assert marker is not None and marker.role == "master" and marker.title == "The Sunken Crown"
    assert marker.rules == "D&D 5e (2024)"
    assert "SRD 5.2" in (root / "campaign.md").read_text()
    assert "# Getting started with The Sunken Crown" in (root / "GETTING_STARTED.md").read_text()
    assert result["git"] == ["Not in a git repository. Snapshots will be zip files."]


def test_create_campaign_allows_folder_with_editor_settings(tmp_path: Path) -> None:
    (tmp_path / ".vscode").mkdir()
    create_campaign(tmp_path, "In Place")
    assert (tmp_path / "campaign.md").is_file()


@pytest.mark.parametrize("setup, message", [("file", "not empty"), ("campaign", "already")])
def test_create_campaign_refuses_used_folders(tmp_path: Path, setup: str, message: str) -> None:
    if setup == "file":
        (tmp_path / "notes.txt").write_text("x")
    else:
        create_campaign(tmp_path, "Existing")
    with pytest.raises(ValueError, match=message):
        create_campaign(tmp_path, "Another")


def test_create_campaign_requires_title(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="title"):
        create_campaign(tmp_path / "x", "   ")


def test_create_campaign_with_git_commits(tmp_path: Path) -> None:
    result = create_campaign(tmp_path / "crown", "Crown", init_git=True)
    assert result["git"] == ["Committed: Create campaign: Crown"]
    assert git(tmp_path / "crown", "status", "--porcelain") == ""


def test_start_campaign_copies_plain_folder(campaign: Path) -> None:
    result = start_campaign(campaign, "Tuesday Group")
    copy = campaign.parent / "sunken-crown--tuesday-group"
    assert result["folder"] == str(copy)
    assert result["method"] == "folder copy"
    assert (copy / "chapters/01-the-drowned-coast/chapter.md").is_file()
    assert (copy / "sessions").is_dir()
    marker = read_marker(copy)
    assert marker is not None
    assert (marker.role, marker.group, marker.source_master) == (
        "running",
        "Tuesday Group",
        str(campaign),
    )
    master_marker = read_marker(campaign)
    assert master_marker is not None and master_marker.role == "master"


def test_start_campaign_clones_git_master(tmp_path: Path) -> None:
    master = tmp_path / "crown"
    create_campaign(master, "Crown", init_git=True)
    head = git(master, "rev-parse", "HEAD")
    result = start_campaign(master, "Friday", tmp_path / "games" / "friday")
    copy = tmp_path / "games" / "friday"
    assert result["method"] == "git clone"
    assert result["git"] == "Committed: Start running copy for Friday"
    assert git(copy, "status", "--porcelain") == ""
    assert git(copy, "remote", "get-url", "origin") == str(master)
    marker = read_marker(copy)
    assert marker is not None and marker.source_commit == head


def test_start_campaign_refuses_dirty_git_master(tmp_path: Path) -> None:
    master = tmp_path / "crown"
    create_campaign(master, "Crown", init_git=True)
    (master / "campaign.md").write_text("# Changed\n")
    with pytest.raises(ValueError, match="uncommitted changes"):
        start_campaign(master, "Friday")


def test_start_campaign_refuses_running_copy(campaign: Path) -> None:
    start_campaign(campaign, "Tuesday")
    with pytest.raises(ValueError, match="already a running copy.*" + campaign.name):
        start_campaign(campaign.parent / "sunken-crown--tuesday", "Again")


def test_start_campaign_refuses_existing_destination_and_non_campaign(
    campaign: Path, tmp_path: Path
) -> None:
    (tmp_path / "taken").mkdir()
    with pytest.raises(ValueError, match="already exists"):
        start_campaign(campaign, "Group", tmp_path / "taken")
    with pytest.raises(ValueError, match="inside the master"):
        start_campaign(campaign, "Group", campaign / "copy")
    with pytest.raises(ValueError, match="no campaign marker"):
        start_campaign(tmp_path / "taken", "Group")


def test_slugify() -> None:
    assert slugify("Tuesday Night: Group #2!") == "tuesday-night-group-2"
    with pytest.raises(ValueError):
        slugify("!!!")


def test_rules_edition_can_be_overridden(tmp_path: Path) -> None:
    create_campaign(tmp_path / "old", "Old", rules="D&D 5e (2014)")
    text = (tmp_path / "old/campaign.md").read_text()
    assert "D&D 5e (2014)." in text and "SRD 5.1" in text
    create_campaign(tmp_path / "other", "Other", rules="Homebrew d20")
    text = (tmp_path / "other/campaign.md").read_text()
    assert "Homebrew d20. Check the license" in text and "SRD" not in text


def test_srd_attribution() -> None:
    assert srd_attribution("D&D 5e (2024)") == SRD_5_2_ATTRIBUTION
    assert srd_attribution("5e, SRD 5.1") == SRD_5_1_ATTRIBUTION
    assert srd_attribution("Pathfinder") is None


def test_ensure_campaign_docs_adds_only_missing_files(campaign: Path) -> None:
    (campaign / "WORKLOG.md").unlink()
    (campaign / "OPEN_ITEMS.md").write_text("# Mine\n")
    result = ensure_campaign_docs(campaign)
    assert result["created"] == ["WORKLOG.md"]
    assert (campaign / "OPEN_ITEMS.md").read_text() == "# Mine\n"
    assert ensure_campaign_docs(campaign)["created"] == []


def test_snapshot_commits_in_git(tmp_path: Path) -> None:
    root = tmp_path / "crown"
    create_campaign(root, "Crown", init_git=True)
    assert snapshot_campaign(root, "Nothing")["result"] == (
        "Nothing has changed since the last commit."
    )
    (root / "campaign.md").write_text("# Crown\n\nMore.\n")
    result = snapshot_campaign(root, "Draft the overview")
    assert result["result"] == "Committed: Snapshot: Draft the overview"
    assert git(root, "log", "-1", "--format=%s") == "Snapshot: Draft the overview"


def test_snapshot_zips_without_git(campaign: Path) -> None:
    import zipfile

    first = snapshot_campaign(campaign, "First pass")
    assert first["method"] == "zip"
    names = zipfile.ZipFile(str(first["archive"])).namelist()
    assert "campaign.md" in names and "SNAPSHOT.txt" in names
    assert not any(name.startswith(".campaign/snapshots") for name in names)


def test_snapshot_requires_campaign_and_summary(campaign: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Describe"):
        snapshot_campaign(campaign, "  ")
    with pytest.raises(ValueError, match="not a campaign, collection, or epic"):
        snapshot_campaign(tmp_path, "x")
