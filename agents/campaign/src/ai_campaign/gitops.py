"""Git for campaigns: repositories and collections of campaigns.

A collection is a git repository whose campaigns, and the running copies started
from them, are submodules. Submodules may themselves contain submodules: starting
a running copy and saving both handle any depth, which the planned epic campaigns
(books, and books split into parts) will build on.

Submodules are recorded with relative local URLs (`./<path>`), so a clone fetches
each submodule from the folder it was cloned from and everything works offline on
one machine. Git refuses local-file submodule clones unless `protocol.file.allow`
is set on the command line or in user config, so every command here passes it.

These are beta defaults and may change after testing; each lives in one place
below (`submodule_url`, `REGISTER_RUNNING_COPIES_IN_COLLECTION`).
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

from ai_campaign.marker import read_marker

COLLECTION_MARKER = Path(".campaign") / "collection.json"
REGISTER_RUNNING_COPIES_IN_COLLECTION = True


def submodule_url(relative_path: str) -> str:
    """The URL recorded for a submodule at `relative_path` inside its superproject."""
    return f"./{relative_path}"


COLLECTION_README = """\
# {title}

A collection of campaigns. Each campaign folder is its own git repository,
registered here as a submodule, so the collection keeps every campaign's
history together.

- Create a campaign in this folder with `/create-campaign` and choose to add
  it to the collection.
- Running copies started from a campaign here are added to the collection
  too.
- To clone the collection with every campaign:
  `git -c protocol.file.allow=always clone --recurse-submodules <collection> <new folder>`
"""


def git(folder: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-c", "protocol.file.allow=always", *args],
            cwd=folder,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise ValueError("git is not installed or not on PATH.") from error


def _failure(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout).strip()


def is_repo(folder: Path) -> bool:
    """True for a repository's top folder, including a submodule (whose .git is a file)."""
    return (folder / ".git").exists()


def init_repo(folder: Path) -> None:
    if not is_repo(folder):
        result = git(folder, "init", "-q")
        if result.returncode != 0:
            raise ValueError(f"git init failed: {_failure(result)}")


def has_changes(folder: Path) -> bool:
    return bool(git(folder, "status", "--porcelain").stdout.strip())


def head(folder: Path) -> str | None:
    result = git(folder, "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def commit_all(folder: Path, message: str) -> str:
    git(folder, "add", "-A")
    result = git(folder, "commit", "-q", "-m", message)
    if result.returncode != 0:
        return f"Files were not committed: {_failure(result)}"
    return f"Committed: {message}"


def commit_paths(folder: Path, message: str, paths: list[str]) -> str:
    """Commit only `paths`, leaving any other changes in `folder` alone."""
    git(folder, "add", "--", *paths)
    result = git(folder, "commit", "-q", "-m", message, "--", *paths)
    if result.returncode != 0:
        return f"Not committed: {_failure(result)}"
    return f"Committed: {message}"


def superproject(folder: Path) -> Path | None:
    """The repository `folder` is registered in as a submodule, if any."""
    result = git(folder, "rev-parse", "--show-superproject-working-tree")
    path = result.stdout.strip()
    return Path(path).resolve() if result.returncode == 0 and path else None


def submodule_paths(folder: Path) -> list[str]:
    """Submodules under `folder`, nested ones included, deepest first."""
    if not (folder / ".gitmodules").is_file():
        return []
    result = git(folder, "submodule", "foreach", "--recursive", "--quiet", "echo $displaypath")
    paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return sorted(paths, key=lambda path: path.count("/"), reverse=True)


def is_collection(folder: Path) -> bool:
    return (folder / COLLECTION_MARKER).is_file()


def collection_for(path: Path) -> Path | None:
    """The collection whose repository would contain `path`, if any."""
    probe = path.parent
    while not probe.exists():
        probe = probe.parent
    result = git(probe, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    top = Path(result.stdout.strip()).resolve()
    return top if is_collection(top) else None


def add_submodule(parent: Path, child: Path, message: str) -> str:
    """Register an existing repository inside `parent` as its submodule, and commit."""
    relative = child.relative_to(parent).as_posix()
    result = git(parent, "submodule", "add", "-q", submodule_url(relative), relative)
    if result.returncode != 0:
        raise ValueError(f"Could not add {relative} as a submodule: {_failure(result)}")
    return commit_paths(parent, message, [".gitmodules", relative])


def attach_submodule_branches(folder: Path) -> None:
    """Put each cloned submodule on a branch, so commits made in it are not left detached."""
    for relative in submodule_paths(folder):
        submodule = folder / relative
        remote_head = git(submodule, "rev-parse", "--abbrev-ref", "origin/HEAD").stdout.strip()
        branch = remote_head.removeprefix("origin/") if remote_head.startswith("origin/") else ""
        git(submodule, "checkout", "-q", "-B", branch or "main")


def info(folder: Path) -> dict[str, object]:
    """How a folder uses git, for campaign_status."""
    try:
        if not is_repo(folder):
            collection = collection_for(folder)
            return {
                "repository": False,
                "inside_collection": str(collection) if collection else None,
            }
        parent = superproject(folder)
        return {
            "repository": True,
            "is_collection": is_collection(folder),
            "registered_in": str(parent) if parent else None,
            "submodules": submodule_paths(folder),
            "uncommitted_changes": has_changes(folder),
        }
    except ValueError as error:
        return {"repository": False, "error": str(error)}


def commit_snapshot(folder: Path, message: str) -> dict[str, object]:
    """Commit a campaign's changes: inside any submodules first, deepest first, then the
    campaign, then the campaign's entry in a collection that contains it."""
    committed = []
    for relative in submodule_paths(folder):
        if has_changes(folder / relative):
            committed.append(f"{relative}: {commit_all(folder / relative, message)}")
    if not committed and not has_changes(folder):
        return {"method": "git", "result": "Nothing has changed since the last commit."}
    result = commit_all(folder, message)
    snapshot: dict[str, object] = {
        "method": "git",
        "result": result,
        "commit": git(folder, "rev-parse", "--short", "HEAD").stdout.strip(),
    }
    if committed:
        snapshot["submodules"] = committed
    parent = superproject(folder)
    if parent is not None:
        relative = folder.relative_to(parent).as_posix()
        snapshot["collection"] = commit_paths(parent, f"{folder.name}: {message}", [relative])
    return snapshot


def create_collection(folder: Path, title: str) -> dict[str, object]:
    """Make a folder a collection: a git repository whose campaigns are submodules."""
    title = " ".join(title.split())
    if not title:
        raise ValueError("The collection needs a title.")
    folder = folder.expanduser().resolve()
    if read_marker(folder) is not None:
        raise ValueError(f"{folder} is a campaign, not a folder of campaigns.")
    if is_collection(folder):
        raise ValueError(f"{folder} is already a collection.")
    folder.mkdir(parents=True, exist_ok=True)
    enclosing = git(folder, "rev-parse", "--show-toplevel")
    if enclosing.returncode == 0 and Path(enclosing.stdout.strip()).resolve() != folder:
        raise ValueError(
            f"{folder} is inside another git repository ({enclosing.stdout.strip()}). Choose "
            "a folder outside it for the collection."
        )

    init_repo(folder)
    created = []
    readme = folder / "README.md"
    if not readme.exists():
        readme.write_text(COLLECTION_README.format(title=title), encoding="utf-8")
        created.append("README.md")
    marker = folder / COLLECTION_MARKER
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(
        json.dumps({"title": title, "created": date.today().isoformat()}, indent=2) + "\n",
        encoding="utf-8",
    )
    created.append(COLLECTION_MARKER.as_posix())
    result = commit_paths(folder, f"Create collection: {title}", created)

    found = [
        {"folder": child.name, "git": is_repo(child)}
        for child in sorted(folder.iterdir())
        if child.is_dir() and read_marker(child) is not None
    ]
    return {"folder": str(folder), "created": created, "git": result, "campaigns_found": found}


def add_to_collection(campaign: Path) -> dict[str, object]:
    """Register an existing campaign inside a collection's folder as its submodule."""
    campaign = campaign.expanduser().resolve()
    marker = read_marker(campaign)
    if marker is None:
        raise ValueError(f"{campaign} is not a campaign; it has no campaign marker.")
    collection = collection_for(campaign)
    if collection is None:
        raise ValueError(
            f"{campaign} is not inside a collection. Create one in its parent folder with "
            "create_collection first."
        )
    if is_repo(campaign) and superproject(campaign) == collection:
        raise ValueError(f"{campaign.name} is already in the collection.")

    steps = []
    if not is_repo(campaign):
        init_repo(campaign)
        steps.append(commit_all(campaign, f"Create campaign: {marker.title}"))
    elif has_changes(campaign):
        raise ValueError(
            "The campaign has uncommitted changes. Save them first (/save-campaign) so the "
            "collection records them."
        )
    if head(campaign) is None:
        steps.append(commit_all(campaign, f"Create campaign: {marker.title}"))
    kind = "running copy" if marker.role == "running" else "campaign"
    steps.append(add_submodule(collection, campaign, f"Add {kind}: {campaign.name}"))
    return {"campaign": str(campaign), "collection": str(collection), "git": steps}
