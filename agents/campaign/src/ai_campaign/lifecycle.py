"""Create master campaigns, start running copies, and snapshot work in progress."""

from __future__ import annotations

import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

from ai_campaign import containers, gitops
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

# Zip snapshots, used only when the campaign is not in a git repository.
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
- `/create-collection` and `/create-epic`: organize several campaigns in
  one folder (see Git, collections, and epics).

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
    encounters/    one file per encounter: CR, XP, stat blocks, and a tracker
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

## Git, collections, and epics

If the campaign is in a git repository, every snapshot is a commit you can
return to, and VS Code's Source Control view shows what changed. Create the
repository first (for example with `git init`), or let the agent do it.

- **Single campaign.** The repository holds this one campaign.
- **Collection.** The repository holds several independent campaigns, each
  in its own subfolder, such as one collection per level range. Run
  `/create-collection` in the repository's folder, then `/create-campaign`
  in a subfolder for each campaign.
- **Epic.** The repository holds the books of one long story, each book a
  campaign in its own subfolder, tied together by `epic.md` and epic-wide
  indexes. Run `/create-epic` in the repository's folder, then
  `/create-campaign` in a subfolder for each book. `/check-epic` checks the
  books against each other.
- `/save-campaign` commits only this campaign's folder, so other campaigns
  in the same repository are never swept in.

## Master and running copies

This folder is the **master** campaign: the campaign as written. Games are
not run from it, because game sessions and the updates after them change
the files. When the campaign is ready to play, `/start-campaign` makes a
**running copy** for one group next to this folder, and you open that copy
to run the group's games. In a collection or epic, the running copy is a
subfolder of the same repository. The master can start any number of
groups.
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


COLLECTION_README = """\
# {title}

A collection of independent campaigns, each in its own subfolder of this git
repository.

- To add a campaign, create a subfolder, open it in VS Code, and run
  `/create-campaign`.
- Running copies started from a campaign here are subfolders too, named
  `<campaign>--<group>`.
- `/save-campaign` in a campaign's folder commits only that campaign.
"""

EPIC_INDEX_DESCRIPTIONS = {
    "npcs.md": "NPCs who matter across the epic: anyone who appears in more than one "
    "book, or whose fate shapes a later book.",
    "items.md": "Magic items and artifacts that matter across the epic.",
    "locations.md": "Places that matter across the epic.",
}

EPIC_INDEX_EXAMPLE = """\
<!--
Add one entry per {kind} that matters across books. Details stay in the books.

## Name
- **Role:** Their part in the epic.
- **Books:** [Book 1](book-folder/campaign.md), [Book 3](other-book/campaign.md)
- **Fate:** What becomes of them, by book, such as "Book 3: dies".
-->
"""

EPIC_GETTING_STARTED = """\
# Getting started with {title}

This folder is an **epic**: one long story told as a series of books. Each
book is a full campaign in its own subfolder. The Campaign Agent keeps the
books consistent with each other and with the epic's story.

## Commands

- `/create-epic`: resume work on the epic as a whole: its story, the book
  order, and the epic-wide indexes.
- `/create-campaign`: run it in a book's subfolder to create or resume that
  book.
- `/check-epic`: check the books against each other, then review the story
  for timeline, character, and foreshadowing problems. It changes nothing.
- `/save-campaign`: save your progress, here for the epic or in a book's
  folder for that book.

Claude Code may show these with a prefix, such as
`/campaign-agent:create-epic`.

## Your epic folder

```text
epic.md            the epic's story, rules edition, and books in reading order
npcs.md            NPCs who matter across books
items.md           items that matter across books
locations.md       places that matter across books
OPEN_ITEMS.md      open questions for the epic as a whole
WORKLOG.md         journal of work on the epic
<book-folder>/     one folder per book, each a full campaign
```

## Adding a book

1. Create a subfolder for the book, such as `02-the-shadow-rising`, and open
   it in VS Code.
2. Run `/create-campaign`. The book uses the epic's rules edition.
3. Add the book to the Books list in `epic.md`, in reading order. The agent
   offers to do this for you.

## Keeping the books consistent

- When an NPC, item, or place matters in more than one book, it belongs in
  the epic's indexes, with the books it appears in and its fate.
- In each book's own indexes, record planned fates in the **Status** field,
  such as "dies in Chapter 3". `/check-epic` uses these to catch, for
  example, an NPC who dies in Book 1 but is a key NPC in Book 2.

## Git

The epic is one git repository. `/save-campaign` in a book's folder commits
only that book; in this folder it commits the whole epic.
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


def _rules_text(rules: str) -> str:
    attribution = srd_attribution(rules)
    if attribution:
        return (
            f"{rules}. Stat blocks come from the open-licensed System Reference Document "
            f"for this edition, or are original.\n\n{attribution}"
        )
    return (
        f"{rules}. Check the license of any game-system material reproduced in this "
        "campaign before sharing or selling it."
    )


def _campaign_md(title: str, rules: str) -> str:
    index_links = "\n".join(f"- [{label}]({name})" for name, label in INDEX_FILES.items())
    rules_text = _rules_text(rules)
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


def _check_new_folder(folder: Path, kind: str) -> Path:
    folder = folder.expanduser().resolve()
    if folder == Path(folder.anchor):
        raise ValueError(f"A {kind} cannot be created at the filesystem root.")
    if folder.exists() and not folder.is_dir():
        raise ValueError(f"{folder} exists and is not a folder.")
    if read_marker(folder) is not None:
        raise ValueError(f"{folder} is already a campaign. Use campaign_status to resume it.")
    if containers.read_container(folder) is not None:
        raise ValueError(f"{folder} is already a collection or epic.")
    enclosing = containers.find_enclosing_campaign(folder)
    if enclosing is not None:
        raise ValueError(f"{folder} is inside the campaign at {enclosing}. Choose another folder.")
    return folder


def _git_setup(folder: Path, init_git: bool, message: str) -> list[str]:
    """Commit a new folder in its repository, creating one first if asked."""
    if gitops.repo_root(folder) is None:
        if not init_git:
            return ["Not in a git repository. Snapshots will be zip files."]
        gitops.init_repo(folder)
    return [gitops.commit_folder(folder, message)]


def create_campaign(
    folder: Path, title: str, rules: str | None = None, init_git: bool = False
) -> dict[str, object]:
    """Set up a new master campaign in an empty or new folder.

    Inside an epic, the campaign is a book and defaults to the epic's rules edition.
    """
    title = " ".join(title.split())
    if not title:
        raise ValueError("The campaign needs a title.")
    folder = _check_new_folder(folder, "campaign")
    if folder.exists():
        existing = sorted(p.name for p in folder.iterdir() if p.name not in ALLOWED_IN_NEW_FOLDER)
        if existing:
            raise ValueError(
                f"{folder} is not empty ({', '.join(existing[:5])}). Choose an empty or new "
                "folder for a new campaign."
            )
    container = containers.find_container(folder)
    if rules is None or not rules.strip():
        rules = (container or {}).get("rules") or DEFAULT_RULES
    rules = " ".join(rules.split())

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
    git_status = _git_setup(folder, init_git, f"Create campaign: {title}")

    result: dict[str, object] = {
        "folder": str(folder),
        "role": "master",
        "rules": rules,
        "created": sorted([*files, marker_path.relative_to(folder).as_posix()]),
        "git": git_status,
    }
    if container is not None:
        result["container"] = {k: container[k] for k in ("kind", "title", "folder")}
        if container["kind"] == containers.EPIC:
            result["next_step"] = "Add this book to the Books list in the epic's epic.md."
    return result


def create_collection(folder: Path, title: str, init_git: bool = False) -> dict[str, object]:
    """Make a folder a collection: independent campaigns in its subfolders."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("The collection needs a title.")
    folder = _check_new_folder(folder, "collection")
    folder.mkdir(parents=True, exist_ok=True)
    created = []
    if not (folder / "README.md").exists():
        (folder / "README.md").write_text(COLLECTION_README.format(title=title), encoding="utf-8")
        created.append("README.md")
    if not (folder / ".gitignore").exists():
        (folder / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
        created.append(".gitignore")
    marker = containers.write_container(
        folder, containers.COLLECTION, {"title": title, "created": date.today().isoformat()}
    )
    created.append(marker.relative_to(folder).as_posix())
    return {
        "folder": str(folder),
        "created": sorted(created),
        "git": _git_setup(folder, init_git, f"Create collection: {title}"),
        "campaigns_found": containers.members(folder),
    }


def _epic_md(title: str, rules: str) -> str:
    index_links = "\n".join(f"- [{label}]({name})" for name, label in INDEX_FILES.items())
    return (
        f"# {title}\n\n"
        f"## Story\n\n{PLACEHOLDER}\n\n"
        f"## Rules\n\n{_rules_text(rules)}\n\n"
        "## Books\n\n"
        "<!--\n"
        "List the books in reading order, each linking to its campaign.md, with its "
        "level range:\n"
        "1. [Book 1: Title](book-folder/campaign.md) - levels 1-4\n"
        "-->\n\n"
        f"## Indexes\n\n{index_links}\n"
    )


def _epic_index_md(name: str) -> str:
    label = INDEX_FILES[name]
    kind = label.removeprefix("Key ").rstrip("s")
    return (
        f"# {label} across the epic\n\n{EPIC_INDEX_DESCRIPTIONS[name]}\n\n"
        + EPIC_INDEX_EXAMPLE.format(kind=kind)
    )


def create_epic(
    folder: Path, title: str, rules: str = DEFAULT_RULES, init_git: bool = False
) -> dict[str, object]:
    """Make a folder an epic: books in its subfolders, tied together by epic.md."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("The epic needs a title.")
    rules = " ".join(rules.split()) or DEFAULT_RULES
    folder = _check_new_folder(folder, "epic")
    if containers.find_container(folder) is not None:
        raise ValueError(f"{folder} is inside a collection or epic. Choose another folder.")
    files = {
        "epic.md": _epic_md(title, rules),
        **{name: _epic_index_md(name) for name in INDEX_FILES},
        GETTING_STARTED_FILE: EPIC_GETTING_STARTED.format(title=title),
        OPEN_ITEMS_FILE: OPEN_ITEMS.replace(
            "- [ ] Decide the campaign's goal. ([campaign.md](campaign.md))\n"
            "- [ ] Write the overview and central story arc. ([campaign.md](campaign.md))\n"
            "- [ ] Outline the chapters.",
            "- [ ] Write the epic's story. ([epic.md](epic.md))\n"
            "- [ ] Decide the books and their order. ([epic.md](epic.md))",
        ).replace("## Chapters\n", "## Books\n"),
        WORKLOG_FILE: WORKLOG.format(today=date.today().isoformat()).replace(
            "Created the campaign.", "Created the epic."
        ),
    }
    if not (folder / ".gitignore").exists():
        files[".gitignore"] = GITIGNORE
    existing = [name for name in files if (folder / name).exists()]
    if existing:
        raise ValueError(f"{folder} already has {', '.join(existing)}. Choose a new folder.")
    _write_files(folder, files)
    marker = containers.write_container(
        folder,
        containers.EPIC,
        {"title": title, "created": date.today().isoformat(), "rules": rules},
    )
    return {
        "folder": str(folder),
        "rules": rules,
        "created": sorted([*files, marker.relative_to(folder).as_posix()]),
        "git": _git_setup(folder, init_git, f"Create epic: {title}"),
        "books_found": containers.members(folder),
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
    """Make a running copy of a master campaign for a group.

    A master at the root of its repository is cloned. A master in a subfolder of a
    repository, such as in a collection or epic, is copied to a sibling folder in
    the same repository and committed there.
    """
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

    root = gitops.repo_root(master)
    source_commit = None
    if root is not None:
        if gitops.has_changes(master):
            raise ValueError(
                "The master has uncommitted changes. Save them first so the running copy "
                "includes them."
            )
        source_commit = gitops.head(master)
        if source_commit is None:
            raise ValueError("The master's git repository has no commits yet. Save it first.")

    if root == master:
        method = "git clone"
        destination.parent.mkdir(parents=True, exist_ok=True)
        clone = gitops.git(destination.parent, "clone", "-q", str(master), str(destination))
        if clone.returncode != 0:
            raise ValueError(f"git clone failed: {(clone.stderr or clone.stdout).strip()}")
    else:
        method = "folder copy"
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

    if gitops.repo_root(destination) is not None:
        git_status = gitops.commit_folder(destination, f"Start running copy for {group}")
        if method == "folder copy":
            method = "folder copy in the same repository"
    else:
        git_status = "Not in a git repository."
    return {
        "folder": str(destination),
        "role": "running",
        "master": str(master),
        "group": group,
        "method": method,
        "git": git_status,
    }


def snapshot_campaign(folder: Path, summary: str) -> dict[str, object]:
    """Save the current state of a campaign, collection, or epic: a commit of just that
    folder in its git repository, or a zip file when it is not in one."""
    folder = folder.expanduser().resolve()
    if read_marker(folder) is None and containers.read_container(folder) is None:
        raise ValueError(f"{folder} is not a campaign, collection, or epic.")
    summary = " ".join(summary.split())
    if not summary:
        raise ValueError("Describe what this snapshot contains in a few words.")

    if gitops.repo_root(folder) is not None:
        result = gitops.commit_folder(folder, f"Snapshot: {summary}")
        return {"method": "git", "result": result, "commit": gitops.head(folder)}

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
