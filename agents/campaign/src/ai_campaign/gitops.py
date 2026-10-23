"""Git for campaigns: one repository, created by the DM, holds everything.

A single campaign, a collection's campaigns, or an epic's books all live in the one
repository. Operations here are scoped to a folder, so saving one campaign commits
only that campaign's files and never sweeps up changes elsewhere in the repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def git(folder: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=folder, capture_output=True, text=True, check=False
        )
    except FileNotFoundError as error:
        raise ValueError("git is not installed or not on PATH.") from error


def _failure(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout).strip()


def _existing(path: Path) -> Path:
    while not path.exists():
        path = path.parent
    return path


def repo_root(folder: Path) -> Path | None:
    """The top folder of the git repository containing `folder`, if any."""
    result = git(_existing(folder), "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def init_repo(folder: Path) -> None:
    result = git(folder, "init", "-q")
    if result.returncode != 0:
        raise ValueError(f"git init failed: {_failure(result)}")


def _scope(folder: Path, root: Path) -> str:
    return folder.resolve().relative_to(root).as_posix() or "."


def has_changes(folder: Path) -> bool:
    """True when anything inside `folder` is uncommitted."""
    root = repo_root(folder)
    if root is None:
        return False
    return bool(git(root, "status", "--porcelain", "--", _scope(folder, root)).stdout.strip())


def head(folder: Path) -> str | None:
    result = git(folder, "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def commit_folder(folder: Path, message: str) -> str:
    """Commit everything inside `folder`, and nothing outside it."""
    root = repo_root(folder)
    if root is None:
        return "Not in a git repository."
    scope = _scope(folder, root)
    git(root, "add", "-A", "--", scope)
    if git(root, "diff", "--cached", "--quiet", "--", scope).returncode == 0:
        return "Nothing has changed since the last commit."
    result = git(root, "commit", "-q", "-m", message, "--", scope)
    if result.returncode != 0:
        return f"Files were not committed: {_failure(result)}"
    return f"Committed: {message}"


def info(folder: Path) -> dict[str, object]:
    """How a folder uses git, for campaign_status."""
    try:
        root = repo_root(folder)
        if root is None:
            return {"repository": None}
        return {
            "repository": str(root),
            "repository_root": root == folder.resolve(),
            "uncommitted_changes": has_changes(folder),
        }
    except ValueError as error:
        return {"repository": None, "error": str(error)}
