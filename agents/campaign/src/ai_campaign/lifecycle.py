"""Create master campaigns and start running copies from them."""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

from ai_campaign.marker import CampaignMarker, read_marker, write_marker
from ai_campaign.structure import (
    CAMPAIGN_FILE,
    CHAPTERS_DIR,
    INDEX_FILES,
    MAPS_DIR,
    PLACEHOLDER,
    SESSIONS_DIR,
)

# Files a new, otherwise empty campaign folder may already contain.
ALLOWED_IN_NEW_FOLDER = {".git", ".vscode", ".DS_Store"}

GITIGNORE = """\
# Secrets never belong in a campaign.
.env

# The Scribe's database and working data. Whether the database should be
# committed is still an open question, so it is excluded for now.
.scribe/
"""

INDEX_DESCRIPTIONS = {
    "npcs.md": "NPCs who matter to the story: allies, villains, quest givers, and anyone "
    "the party must meet again.",
    "items.md": "Magic items and artifacts that matter to the story.",
    "locations.md": "Places that matter to the story: cities, dungeons, strongholds, and "
    "important sites.",
}

INDEX_ENTRY_EXAMPLE = """\
<!--
Add one entry per key {kind}. Full details stay in the linked sections.

## Name
- **Role:** Their part in the story.
- **Description:** A short description.
- **Appears in:** [Chapter 1](chapters/01-chapter-name/chapter.md)
- **Status:** Kept current in a running copy, such as alive or dead.
-->
"""


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError("The name must contain at least one letter or digit.")
    return slug


def _git(folder: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=folder, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as error:
        raise ValueError("git is not installed or not on PATH.") from error


def _commit_all(folder: Path, message: str) -> str:
    _git(folder, "add", "-A")
    result = _git(folder, "commit", "-q", "-m", message)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return f"Files were not committed: {detail}"
    return f"Committed: {message}"


def _campaign_md(title: str) -> str:
    index_links = "\n".join(f"- [{label}]({name})" for name, label in INDEX_FILES.items())
    return (
        f"# {title}\n\n"
        f"## Goal\n\n{PLACEHOLDER}\n\n"
        f"## Overview\n\n{PLACEHOLDER}\n\n"
        f"## Chapters\n\n{PLACEHOLDER}\n\n"
        f"## Indexes\n\n{index_links}\n"
    )


def _index_md(name: str) -> str:
    label = INDEX_FILES[name]
    kind = label.removeprefix("Key ").rstrip("s")
    return f"# {label}\n\n{INDEX_DESCRIPTIONS[name]}\n\n" + INDEX_ENTRY_EXAMPLE.format(kind=kind)


def create_campaign(folder: Path, title: str, init_git: bool = False) -> dict[str, object]:
    """Set up a new master campaign in an empty or new folder."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("The campaign needs a title.")
    folder = folder.expanduser().resolve()
    if folder == Path(folder.anchor):
        raise ValueError("A campaign cannot be created at the filesystem root.")
    if folder.exists():
        if not folder.is_dir():
            raise ValueError(f"{folder} exists and is not a folder.")
        if read_marker(folder) is not None:
            raise ValueError(f"{folder} is already a campaign. Use campaign_status to resume it.")
        existing = sorted(p.name for p in folder.iterdir() if p.name not in ALLOWED_IN_NEW_FOLDER)
        if existing:
            raise ValueError(
                f"{folder} is not empty ({', '.join(existing[:5])}). Choose an empty or new "
                "folder for a new campaign."
            )

    files = {
        CAMPAIGN_FILE: _campaign_md(title),
        **{name: _index_md(name) for name in INDEX_FILES},
        ".gitignore": GITIGNORE,
        f"{MAPS_DIR}/.gitkeep": "",
        f"{CHAPTERS_DIR}/.gitkeep": "",
    }
    for relative, content in files.items():
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    marker = CampaignMarker(role="master", title=title, created=date.today().isoformat())
    marker_path = write_marker(folder, marker)

    git_status = "Not a git repository."
    if init_git:
        if not (folder / ".git").exists():
            result = _git(folder, "init", "-q")
            if result.returncode != 0:
                raise ValueError(f"git init failed: {result.stderr.strip()}")
        git_status = _commit_all(folder, f"Create campaign: {title}")

    created = sorted([*files, marker_path.relative_to(folder).as_posix()])
    return {"folder": str(folder), "role": "master", "created": created, "git": git_status}


def start_campaign(
    master: Path, group: str, destination: Path | None = None
) -> dict[str, object]:
    """Make a running copy of a master campaign for a group."""
    master = master.expanduser().resolve()
    marker = read_marker(master)
    if marker is None:
        raise ValueError(f"{master} is not a campaign; it has no campaign marker.")
    if marker.role != "master":
        source = f" Start from its master instead: {marker.source_master}" if (
            marker.source_master
        ) else ""
        raise ValueError(f"{master} is already a running copy.{source}")
    group = " ".join(group.split())
    if not group:
        raise ValueError("Name the group this running copy is for.")

    destination = (
        destination.expanduser().resolve()
        if destination
        else master.parent / f"{master.name}--{slugify(group)}"
    )
    if destination.exists():
        raise ValueError(f"{destination} already exists. Choose another location or group name.")
    if destination.is_relative_to(master):
        raise ValueError("The running copy cannot be inside the master campaign folder.")

    uses_git = (master / ".git").exists()
    source_commit = None
    if uses_git:
        status = _git(master, "status", "--porcelain")
        if status.stdout.strip():
            raise ValueError(
                "The master has uncommitted changes. Commit them first so the running copy "
                "includes them."
            )
        head = _git(master, "rev-parse", "HEAD")
        if head.returncode != 0:
            raise ValueError("The master git repository has no commits yet. Commit it first.")
        source_commit = head.stdout.strip()
        clone = _git(master.parent, "clone", "-q", str(master), str(destination))
        if clone.returncode != 0:
            raise ValueError(f"git clone failed: {clone.stderr.strip()}")
    else:
        shutil.copytree(
            master, destination, ignore=shutil.ignore_patterns(".git", ".scribe", SESSIONS_DIR)
        )

    (destination / SESSIONS_DIR).mkdir(exist_ok=True)
    (destination / SESSIONS_DIR / ".gitkeep").touch()
    marker.role = "running"
    marker.source_master = str(master)
    marker.source_commit = source_commit
    marker.group = group
    marker.started = date.today().isoformat()
    write_marker(destination, marker)

    git_status = "Plain folder copy; the master is not a git repository."
    if uses_git:
        git_status = _commit_all(destination, f"Start running copy for {group}")
    return {
        "folder": str(destination),
        "role": "running",
        "master": str(master),
        "group": group,
        "method": "git clone" if uses_git else "folder copy",
        "git": git_status,
    }
