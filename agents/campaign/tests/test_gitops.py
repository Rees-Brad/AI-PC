from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_campaign import gitops
from ai_campaign.lifecycle import create_campaign, snapshot_campaign, start_campaign


def git(folder: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "protocol.file.allow=always", *args],
        cwd=folder, capture_output=True, text=True, check=True,
    ).stdout.strip()


def submodules(folder: Path) -> list[str]:
    return sorted(
        line.split()[1] for line in git(folder, "submodule", "status").splitlines()
    )


@pytest.fixture
def collection(tmp_path: Path) -> Path:
    root = tmp_path / "Campaigns"
    gitops.create_collection(root, "My Campaigns")
    return root


def test_create_collection(collection: Path) -> None:
    assert gitops.is_collection(collection)
    assert "# My Campaigns" in (collection / "README.md").read_text()
    assert git(collection, "status", "--porcelain") == ""
    assert git(collection, "log", "-1", "--format=%s") == "Create collection: My Campaigns"


def test_create_collection_lists_existing_campaigns(tmp_path: Path) -> None:
    root = tmp_path / "Campaigns"
    create_campaign(root / "old", "Old")
    create_campaign(root / "older", "Older", git="repo")
    result = gitops.create_collection(root, "Mine")
    assert result["campaigns_found"] == [
        {"folder": "old", "git": False},
        {"folder": "older", "git": True},
    ]


def test_create_collection_refusals(tmp_path: Path, collection: Path) -> None:
    with pytest.raises(ValueError, match="already a collection"):
        gitops.create_collection(collection, "Again")
    with pytest.raises(ValueError, match="inside another git repository"):
        gitops.create_collection(collection / "nested", "Nested")
    create_campaign(tmp_path / "solo", "Solo")
    with pytest.raises(ValueError, match="is a campaign"):
        gitops.create_collection(tmp_path / "solo", "Nope")


def test_campaign_created_as_submodule_of_collection(collection: Path) -> None:
    result = create_campaign(collection / "crown", "Crown", git="submodule")
    assert result["git"] == ["Committed: Create campaign: Crown", "Committed: Add campaign: crown"]
    assert submodules(collection) == ["crown"]
    assert git(collection, "config", "-f", ".gitmodules", "submodule.crown.url") == "./crown"
    assert gitops.superproject(collection / "crown") == collection
    assert git(collection, "status", "--porcelain") == ""


def test_submodule_mode_needs_a_collection(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not inside a collection"):
        create_campaign(tmp_path / "crown", "Crown", git="submodule")
    with pytest.raises(ValueError, match="git must be one of"):
        create_campaign(tmp_path / "x", "X", git="yes")


def test_repo_inside_collection_is_flagged_not_registered(collection: Path) -> None:
    result = create_campaign(collection / "crown", "Crown", git="repo")
    assert "Use add_to_collection" in result["git"][-1]
    assert submodules(collection) == []


def test_add_existing_campaign_to_collection(collection: Path) -> None:
    create_campaign(collection / "plain", "Plain")
    result = gitops.add_to_collection(collection / "plain")
    assert result["git"] == ["Committed: Create campaign: Plain", "Committed: Add campaign: plain"]
    assert submodules(collection) == ["plain"]
    with pytest.raises(ValueError, match="already in the collection"):
        gitops.add_to_collection(collection / "plain")


def test_add_to_collection_refusals(tmp_path: Path, collection: Path) -> None:
    create_campaign(tmp_path / "outside", "Outside")
    with pytest.raises(ValueError, match="not inside a collection"):
        gitops.add_to_collection(tmp_path / "outside")
    create_campaign(collection / "dirty", "Dirty", git="repo")
    (collection / "dirty/campaign.md").write_text("# Changed\n")
    with pytest.raises(ValueError, match="uncommitted changes"):
        gitops.add_to_collection(collection / "dirty")


def test_running_copy_is_added_to_the_collection(collection: Path) -> None:
    create_campaign(collection / "crown", "Crown", git="submodule")
    result = start_campaign(collection / "crown", "Tuesday")
    assert result["git"][-1] == "Committed: Add running copy: crown--tuesday"
    assert submodules(collection) == ["crown", "crown--tuesday"]
    assert git(collection, "status", "--porcelain") == ""


def nest_submodule(campaign: Path, relative: str) -> Path:
    """Make a folder inside a campaign its own repository, registered as a submodule.

    There is no tool for this in this release; it stands in for the planned epic
    campaigns, so starting and saving are tested with nested submodules.
    """
    folder = campaign / relative
    (folder / "adventures").mkdir(parents=True)
    (folder / "chapter.md").write_text("# Part\n")
    (folder / "adventures/01-start.md").write_text("# Start\n")
    git(folder, "init", "-q")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "Part")
    git(campaign, "submodule", "add", "-q", f"./{relative}", relative)
    git(campaign, "commit", "-q", "-m", f"Add {relative}")
    return folder


def test_running_copy_and_snapshot_with_nested_submodules(collection: Path) -> None:
    campaign = collection / "crown"
    create_campaign(campaign, "Crown", git="submodule")
    nest_submodule(campaign, "chapters/01-the-coast")
    git(collection, "commit", "-q", "-am", "Update crown")

    copy = Path(str(start_campaign(campaign, "Tuesday")["folder"]))
    part = copy / "chapters/01-the-coast"
    assert (part / "adventures/01-start.md").is_file()
    assert git(part, "rev-parse", "--abbrev-ref", "HEAD") != "HEAD"  # on a branch
    assert gitops.info(copy)["submodules"] == ["chapters/01-the-coast"]

    (part / "adventures/01-start.md").write_text("# Start, revised\n")
    result = snapshot_campaign(copy, "After session 1")

    assert result["submodules"] == ["chapters/01-the-coast: Committed: Snapshot: After session 1"]
    assert result["collection"] == "Committed: crown--tuesday: Snapshot: After session 1"
    assert git(part, "status", "--porcelain") == ""
    assert git(copy, "status", "--porcelain") == ""
    assert git(collection, "status", "--porcelain") == ""


def test_unsaved_change_in_a_nested_submodule_blocks_starting(tmp_path: Path) -> None:
    campaign = tmp_path / "crown"
    create_campaign(campaign, "Crown", git="repo")
    part = nest_submodule(campaign, "chapters/01-a")
    (part / "chapter.md").write_text("# Changed\n")
    with pytest.raises(ValueError, match="uncommitted changes"):
        start_campaign(campaign, "G")


def test_info_for_plain_folders(tmp_path: Path, collection: Path) -> None:
    assert gitops.info(tmp_path) == {"repository": False, "inside_collection": None}
    create_campaign(collection / "plain", "Plain")
    assert gitops.info(collection / "plain")["inside_collection"] == str(collection)
