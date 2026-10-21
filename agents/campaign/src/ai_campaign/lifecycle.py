"""Create master campaigns, start running copies, and snapshot work in progress."""

from __future__ import annotations

import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

from ai_campaign import gitops
from ai_campaign.marker import CampaignMarker, read_marker, write_marker
from ai_campaign.structure import (
    CAMPAIGN_FILE,
    CHAPTERS_DIR,
    GETTING_STARTED_FILE,
    INDEX_FILES,
    MAPS_DIR,
    OPEN_ITEMS_FILE,
    PLACEHOLDER,
    SESSIONS_DIR,
    WORKLOG_FILE,
)

DEFAULT_RULES = "D&D 5e (2024)"
# How a new campaign uses git: not at all, as its own repository, or as its own
# repository registered in the collection that contains it.
GIT_MODES = ("none", "repo", "submodule")
SNAPSHOTS_DIR = Path(".campaign") / "snapshots"

# Files a new, otherwise empty campaign folder may already contain.
ALLOWED_IN_NEW_FOLDER = {".git", ".vscode", ".DS_Store"}

SRD_5_2_ATTRIBUTION = (
    "This work includes material from the System Reference Document 5.2 (\"SRD 5.2\") by "
    "Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is "
    "licensed under the Creative Commons Attribution 4.0 International License, available "
    "at https://creativecommons.org/licenses/by/4.0/legalcode."
)
SRD_5_1_ATTRIBUTION = (
    "This work includes material taken from the System Reference Document 5.1 (\"SRD 5.1\") "
    "by Wizards of the Coast LLC and available at "
    "https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed "
    "under the Creative Commons Attribution 4.0 International License available at "
    "https://creativecommons.org/licenses/by/4.0/legalcode."
)

GITIGNORE = """\
# Secrets never belong in a campaign.
.env

# The Scribe's database and working data. Whether the database should be
# committed is still an open question, so it is excluded for now.
.scribe/

# Zip snapshots, used only when the campaign is not a git repository.
.campaign/snapshots/
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

GETTING_STARTED = """\
# Getting started with {title}

The Campaign Agent works with you on this campaign in the Claude Code panel.
Talk to it in plain language; it asks questions, offers options, and drafts
the files. You make the decisions, and every change is shown to you for
approval before it is written.

## Commands

- `/create-campaign`: resume work on this campaign. The agent reads the
  work log and open items and suggests what to do next.
- `/check-campaign`: look for broken links, unlinked maps, and other
  structure problems. It changes nothing.
- `/save-campaign`: save your progress. The agent updates the work log and
  open items, checks the campaign, and takes a snapshot.
- `/start-campaign`: when the campaign is ready to play, make a running
  copy for a group.
- `/create-collection`: organize a folder of campaigns as one git
  repository (see Git and collections).

Claude Code may show these with a prefix, such as
`/campaign-agent:create-campaign`.

## Working across several days

Building a campaign takes many sittings.

- Before you stop, run `/save-campaign`. The agent records what was done
  and decided in `WORKLOG.md`, updates `OPEN_ITEMS.md`, and takes a
  snapshot you can return to.
- Next time, open this folder and run `/create-campaign`. The agent picks
  up from the work log and open items.
- Earlier conversations are saved too. Reopen one from the past
  conversations button in the Claude Code panel, or with `/resume`.

## Files the agent keeps for you

- `OPEN_ITEMS.md` lists open questions and unfinished parts. The agent
  checks items off as they are done. Reorder items or mark them
  **(priority)** to tell the agent what to work on first, and add your own.
- `WORKLOG.md` is a short journal of each working session: what was done,
  what was decided and why, and ideas set aside for later.
- This file is a reference you can return to at any time.

## Your campaign folder

```text
campaign.md        goal, overview, rules edition, and links to every chapter
npcs.md            key NPCs
items.md           key magic items and artifacts
locations.md       key locations
maps/              map images (PNG, JPEG, or WebP)
chapters/
  01-<chapter>/
    chapter.md     the chapter outline
    adventures/    one file per adventure
    encounters/    one file per encounter, with stat blocks and a tracker
```

Every section is its own file, numbered in story order.

## A good layout in VS Code

- Keep the Explorer open on the left to see the whole campaign.
- Open a chapter, adventure, or encounter and press Ctrl+Shift+V
  (Cmd+Shift+V on a Mac) to read it as formatted text.
- Open the section's map beside it: drag the map's tab to the side of the
  editor.
- Keep the Claude Code panel open on the right.

## Maps

Make and edit maps in any tool, then save them into `maps/` as PNG, JPEG,
or WebP. Ask the agent to add a map to a section, and to answer questions
about it. Saving an edited map under the same name keeps every link to it
working.

## Git and collections

If the campaign uses git, every snapshot is a commit you can return to, and
VS Code's Source Control view shows what changed.

- **Collections.** A folder of campaigns, such as `~/Campaigns/levels-1-3`,
  can be a collection: a git repository in which each campaign is its own
  repository, registered as a submodule. Run `/create-collection` in that
  folder. New campaigns created inside it, and running copies started from
  them, are added automatically.
- `/save-campaign` and `/start-campaign` handle the submodules for you, so
  you never need to run git yourself.
- If you do run git commands yourself on submodules, such as
  `git clone --recurse-submodules`, add `-c protocol.file.allow=always`, for
  example `git -c protocol.file.allow=always clone --recurse-submodules ...`.
  Git blocks copying submodules from local folders by default and reports
  "transport 'file' not allowed". The agent adds the flag to its own
  commands and leaves your git settings alone.

## Master and running copies

This folder is the **master** campaign: the campaign as written. Games are
not run from it, because game sessions and the updates after them change
the files. When the campaign is ready to play, `/start-campaign` makes a
**running copy** for one group next to this folder, and you open that copy
to run the group's games. The master can start any number of groups.
"""

OPEN_ITEMS = f"""\
# Open items

The Campaign Agent keeps this list up to date as you work and checks items
off when they are done. Reorder items or mark them **(priority)** to tell
the agent what to work on first, and add your own at any time.

## Story and goal

- [ ] Decide the campaign's goal. ([campaign.md]({CAMPAIGN_FILE}))
- [ ] Write the overview and central story arc. ([campaign.md]({CAMPAIGN_FILE}))
- [ ] Outline the chapters.

## Chapters

## NPCs, items, and locations

## Maps

## Done
"""

WORKLOG = """\
# Work log

The Campaign Agent adds an entry at the end of each working session: what
was done, what was decided and why, and ideas set aside for later. Newest
entries come first.

## {today}

- Created the campaign.
"""


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError("The name must contain at least one letter or digit.")
    return slug


def srd_attribution(rules: str) -> str | None:
    """The attribution statement for the open-licensed SRD that matches a rules edition."""
    lowered = rules.lower()
    if "2024" in lowered or "5.2" in lowered:
        return SRD_5_2_ATTRIBUTION
    if "2014" in lowered or "5.1" in lowered:
        return SRD_5_1_ATTRIBUTION
    return None


def _campaign_md(title: str, rules: str) -> str:
    index_links = "\n".join(f"- [{label}]({name})" for name, label in INDEX_FILES.items())
    attribution = srd_attribution(rules)
    if attribution:
        rules_text = (
            f"{rules}. Stat blocks come from the open-licensed System Reference Document "
            f"for this edition, or are original.\n\n{attribution}"
        )
    else:
        rules_text = (
            f"{rules}. Check the license of any game-system material reproduced in this "
            "campaign before sharing or selling it."
        )
    return (
        f"# {title}\n\n"
        f"## Goal\n\n{PLACEHOLDER}\n\n"
        f"## Overview\n\n{PLACEHOLDER}\n\n"
        f"## Rules\n\n{rules_text}\n\n"
        f"## Chapters\n\n{PLACEHOLDER}\n\n"
        f"## Indexes\n\n{index_links}\n"
    )


def _index_md(name: str) -> str:
    label = INDEX_FILES[name]
    kind = label.removeprefix("Key ").rstrip("s")
    return f"# {label}\n\n{INDEX_DESCRIPTIONS[name]}\n\n" + INDEX_ENTRY_EXAMPLE.format(kind=kind)


def _agent_docs(title: str) -> dict[str, str]:
    return {
        GETTING_STARTED_FILE: GETTING_STARTED.format(title=title),
        OPEN_ITEMS_FILE: OPEN_ITEMS,
        WORKLOG_FILE: WORKLOG.format(today=date.today().isoformat()),
    }


def _write_files(folder: Path, files: dict[str, str]) -> None:
    for relative, content in files.items():
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _require_campaign(folder: Path) -> CampaignMarker:
    marker = read_marker(folder)
    if marker is None:
        raise ValueError(f"{folder} is not a campaign; it has no campaign marker.")
    return marker


def create_campaign(
    folder: Path, title: str, git: str = "none", rules: str = DEFAULT_RULES
) -> dict[str, object]:
    """Set up a new master campaign in an empty or new folder."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("The campaign needs a title.")
    if git not in GIT_MODES:
        raise ValueError(f"git must be one of {', '.join(GIT_MODES)}.")
    rules = " ".join(rules.split()) or DEFAULT_RULES
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
    collection = gitops.collection_for(folder)
    if git == "submodule" and collection is None:
        raise ValueError(
            f"{folder} is not inside a collection. Create one in the parent folder with "
            "create_collection, or use git='repo'."
        )

    files = {
        CAMPAIGN_FILE: _campaign_md(title, rules),
        **{name: _index_md(name) for name in INDEX_FILES},
        **_agent_docs(title),
        ".gitignore": GITIGNORE,
        f"{MAPS_DIR}/.gitkeep": "",
        f"{CHAPTERS_DIR}/.gitkeep": "",
    }
    _write_files(folder, files)
    marker = CampaignMarker(
        role="master", title=title, created=date.today().isoformat(), rules=rules
    )
    marker_path = write_marker(folder, marker)

    git_status = ["Not a git repository."]
    if git != "none":
        gitops.init_repo(folder)
        git_status = [gitops.commit_all(folder, f"Create campaign: {title}")]
    if git == "submodule" and collection is not None:
        git_status.append(gitops.add_submodule(collection, folder, f"Add campaign: {folder.name}"))
    elif collection is not None:
        git_status.append(
            f"This campaign is inside the collection at {collection} but not part of it. "
            "Use add_to_collection to add it."
        )

    created = sorted([*files, marker_path.relative_to(folder).as_posix()])
    return {
        "folder": str(folder),
        "role": "master",
        "rules": rules,
        "created": created,
        "git": git_status,
    }


def ensure_campaign_docs(folder: Path) -> dict[str, object]:
    """Add GETTING_STARTED.md, OPEN_ITEMS.md, and WORKLOG.md if missing; never overwrite."""
    folder = folder.expanduser().resolve()
    marker = _require_campaign(folder)
    missing = {
        name: content
        for name, content in _agent_docs(marker.title).items()
        if not (folder / name).exists()
    }
    _write_files(folder, missing)
    return {"folder": str(folder), "created": sorted(missing)}


def start_campaign(
    master: Path, group: str, destination: Path | None = None
) -> dict[str, object]:
    """Make a running copy of a master campaign for a group."""
    master = master.expanduser().resolve()
    marker = _require_campaign(master)
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

    uses_git = gitops.is_repo(master)
    source_commit = None
    if uses_git:
        if gitops.has_changes(master) or any(
            gitops.has_changes(master / path) for path in gitops.submodule_paths(master)
        ):
            raise ValueError(
                "The master has uncommitted changes. Commit them first so the running copy "
                "includes them."
            )
        source_commit = gitops.head(master)
        if source_commit is None:
            raise ValueError("The master git repository has no commits yet. Commit it first.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        clone = gitops.git(
            destination.parent, "clone", "-q", "--recurse-submodules", str(master),
            str(destination),
        )
        if clone.returncode != 0:
            raise ValueError(f"git clone failed: {(clone.stderr or clone.stdout).strip()}")
        gitops.attach_submodule_branches(destination)
    else:
        shutil.copytree(
            master,
            destination,
            ignore=shutil.ignore_patterns(".git", ".scribe", SESSIONS_DIR, "snapshots"),
        )

    (destination / SESSIONS_DIR).mkdir(exist_ok=True)
    (destination / SESSIONS_DIR / ".gitkeep").touch()
    marker.role = "running"
    marker.source_master = str(master)
    marker.source_commit = source_commit
    marker.group = group
    marker.started = date.today().isoformat()
    write_marker(destination, marker)

    git_status = ["Plain folder copy; the master is not a git repository."]
    if uses_git:
        git_status = [gitops.commit_all(destination, f"Start running copy for {group}")]
        collection = gitops.collection_for(destination)
        if collection is not None and gitops.REGISTER_RUNNING_COPIES_IN_COLLECTION:
            message = f"Add running copy: {destination.name}"
            git_status.append(gitops.add_submodule(collection, destination, message))
    return {
        "folder": str(destination),
        "role": "running",
        "master": str(master),
        "group": group,
        "method": "git clone" if uses_git else "folder copy",
        "git": git_status,
    }


def snapshot_campaign(folder: Path, summary: str) -> dict[str, object]:
    """Save the campaign's current state: a git commit, or a zip file without git."""
    folder = folder.expanduser().resolve()
    _require_campaign(folder)
    summary = " ".join(summary.split())
    if not summary:
        raise ValueError("Describe what this snapshot contains in a few words.")

    if gitops.is_repo(folder):
        return gitops.commit_snapshot(folder, f"Snapshot: {summary}")

    snapshots = folder / SNAPSHOTS_DIR
    snapshots.mkdir(parents=True, exist_ok=True)
    archive = snapshots / f"{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("SNAPSHOT.txt", summary + "\n")
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(folder)
            if path.is_file() and not relative.is_relative_to(SNAPSHOTS_DIR):
                bundle.write(path, relative.as_posix())
    return {
        "method": "zip",
        "result": f"Saved {archive.relative_to(folder).as_posix()}",
        "archive": str(archive),
    }
