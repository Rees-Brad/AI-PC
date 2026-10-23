"""Single campaigns, collections, and epics in one git repository created by the DM."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_campaign import containers, gitops
from ai_campaign.lifecycle import (
    create_campaign,
    create_collection,
    create_epic,
    snapshot_campaign,
    start_campaign,
)
from ai_campaign.marker import read_marker


def git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=folder, capture_output=True, text=True, check=True
    ).stdout.strip()


def make_repo(folder: Path) -> Path:
    folder.mkdir(parents=True)
    git(folder, "init", "-q")
    return folder


@pytest.fixture
def collection(tmp_path: Path) -> Path:
    root = make_repo(tmp_path / "levels-1-3")
    create_collection(root, "Levels 1-3")
    return root


def test_campaign_in_a_repo_the_dm_created(tmp_path: Path) -> None:
    root = make_repo(tmp_path / "crown")
    result = create_campaign(root, "Crown")
    assert result["git"] == ["Committed: Create campaign: Crown"]
    assert git(root, "status", "--porcelain") == ""
    assert gitops.info(root) == {
        "repository": str(root), "repository_root": True, "uncommitted_changes": False,
    }


def test_init_git_creates_the_repository_when_asked(tmp_path: Path) -> None:
    result = create_campaign(tmp_path / "crown", "Crown", init_git=True)
    assert result["git"] == ["Committed: Create campaign: Crown"]
    assert gitops.repo_root(tmp_path / "crown") == tmp_path / "crown"


def test_without_a_repository_snapshots_are_zips(tmp_path: Path) -> None:
    result = create_campaign(tmp_path / "crown", "Crown")
    assert result["git"] == ["Not in a git repository. Snapshots will be zip files."]
    assert snapshot_campaign(tmp_path / "crown", "First")["method"] == "zip"


def test_create_collection(collection: Path) -> None:
    assert containers.read_container(collection)["kind"] == "collection"
    assert "# Levels 1-3" in (collection / "README.md").read_text()
    assert git(collection, "status", "--porcelain") == ""


def test_collection_lists_campaigns_already_there(tmp_path: Path) -> None:
    root = make_repo(tmp_path / "shelf")
    create_campaign(root / "old", "Old")
    result = create_collection(root, "Shelf")
    assert result["campaigns_found"] == [{"folder": "old", "title": "Old", "role": "master"}]


def test_campaigns_in_a_collection_are_committed_separately(collection: Path) -> None:
    create_campaign(collection / "crown", "Crown")
    create_campaign(collection / "keep", "Keep")
    assert containers.find_container(collection / "crown")["title"] == "Levels 1-3"

    (collection / "crown/campaign.md").write_text("# Crown, revised\n")
    (collection / "keep/campaign.md").write_text("# Keep, revised\n")
    result = snapshot_campaign(collection / "crown", "Revise crown")

    assert result["result"] == "Committed: Snapshot: Revise crown"
    assert git(collection, "status", "--porcelain") == "M keep/campaign.md"
    assert snapshot_campaign(collection / "crown", "Again")["result"] == (
        "Nothing has changed since the last commit."
    )


def test_running_copy_in_a_collection_is_a_sibling_folder(collection: Path) -> None:
    create_campaign(collection / "crown", "Crown")
    head = git(collection, "rev-parse", "HEAD")
    result = start_campaign(collection / "crown", "Tuesday")

    copy = collection / "crown--tuesday"
    assert result["method"] == "folder copy in the same repository"
    assert result["git"] == "Committed: Start running copy for Tuesday"
    assert (copy / "sessions").is_dir()
    marker = read_marker(copy)
    assert marker is not None and marker.role == "running" and marker.source_commit == head
    assert git(collection, "status", "--porcelain") == ""


def test_unsaved_master_in_a_collection_blocks_starting(collection: Path) -> None:
    create_campaign(collection / "crown", "Crown")
    (collection / "crown/campaign.md").write_text("# Changed\n")
    with pytest.raises(ValueError, match="uncommitted changes"):
        start_campaign(collection / "crown", "Tuesday")
    # Unsaved work in another campaign does not block this one.
    create_campaign(collection / "keep", "Keep")
    (collection / "keep/campaign.md").write_text("# Changed\n")
    git(collection, "checkout", "--", "crown/campaign.md")
    start_campaign(collection / "crown", "Tuesday")


def test_folders_cannot_nest_inside_a_campaign(tmp_path: Path) -> None:
    create_campaign(tmp_path / "crown", "Crown")
    for create, args in [
        (create_campaign, ("Inner",)),
        (create_collection, ("Inner",)),
        (create_epic, ("Inner",)),
    ]:
        with pytest.raises(ValueError, match="inside the campaign"):
            create(tmp_path / "crown/chapters/inner", *args)


def test_container_refusals(collection: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="already a collection or epic"):
        create_collection(collection, "Again")
    with pytest.raises(ValueError, match="inside a collection or epic"):
        create_epic(collection / "saga", "Saga")
    create_campaign(tmp_path / "solo", "Solo")
    with pytest.raises(ValueError, match="already a campaign"):
        create_collection(tmp_path / "solo", "Nope")


def test_create_epic_and_a_book(tmp_path: Path) -> None:
    root = make_repo(tmp_path / "saga")
    result = create_epic(root, "The Long Road", rules="D&D 5e (2014)")
    assert result["created"] == [
        ".campaign/epic.json", ".gitignore", "GETTING_STARTED.md", "OPEN_ITEMS.md",
        "WORKLOG.md", "epic.md", "items.md", "locations.md", "npcs.md",
    ]
    assert "## Books" in (root / "epic.md").read_text()
    assert "SRD 5.1" in (root / "epic.md").read_text()
    assert "Write the epic's story" in (root / "OPEN_ITEMS.md").read_text()
    assert "# Getting started with The Long Road" in (root / "GETTING_STARTED.md").read_text()

    book = create_campaign(root / "01-the-start", "The Start")
    assert book["rules"] == "D&D 5e (2014)"
    assert book["container"]["kind"] == "epic"
    assert "Books list" in str(book["next_step"])
    assert git(root, "status", "--porcelain") == ""


def test_snapshot_of_an_epic_commits_all_its_books(tmp_path: Path) -> None:
    root = make_repo(tmp_path / "saga")
    create_epic(root, "Saga")
    create_campaign(root / "01-a", "A")
    (root / "01-a/campaign.md").write_text("# A, revised\n")
    (root / "epic.md").write_text("# Saga, revised\n")
    assert snapshot_campaign(root, "Revise")["result"] == "Committed: Snapshot: Revise"
    assert git(root, "status", "--porcelain") == ""


def test_snapshot_needs_a_campaign_collection_or_epic(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a campaign, collection, or epic"):
        snapshot_campaign(tmp_path, "x")
