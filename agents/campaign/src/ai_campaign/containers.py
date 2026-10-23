"""Collections and epics: folders that hold campaigns.

A collection holds independent campaigns. An epic holds books: campaigns told in
order, tied together by the epic's story and indexes. Each is marked by a file in
its `.campaign/` folder, and its campaigns are ordinary subfolders.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_campaign.marker import read_marker

COLLECTION = "collection"
EPIC = "epic"
CONTAINER_MARKERS = {
    COLLECTION: Path(".campaign") / "collection.json",
    EPIC: Path(".campaign") / "epic.json",
}


def read_container(folder: Path) -> dict[str, Any] | None:
    """The container marker in `folder`, with its kind, or None."""
    for kind, relative in CONTAINER_MARKERS.items():
        path = folder / relative
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(f"The {kind} marker {relative} is not valid JSON.") from error
            return {**data, "kind": kind, "folder": str(folder.resolve())}
    return None


def write_container(folder: Path, kind: str, data: dict[str, Any]) -> Path:
    path = folder / CONTAINER_MARKERS[kind]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _ancestors(folder: Path) -> list[Path]:
    return list(folder.resolve().parents)


def find_container(folder: Path) -> dict[str, Any] | None:
    """The nearest collection or epic that contains `folder`, not counting itself."""
    for parent in _ancestors(folder):
        container = read_container(parent)
        if container is not None:
            return container
    return None


def find_enclosing_campaign(folder: Path) -> Path | None:
    """A campaign folder that contains `folder`, not counting itself."""
    for parent in _ancestors(folder):
        if (parent / ".campaign" / "campaign.json").is_file():
            return parent
    return None


def members(container: Path) -> list[dict[str, Any]]:
    """Campaigns directly inside a collection or epic, with their role."""
    found = []
    for child in sorted(container.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            marker = read_marker(child)
            if marker is not None:
                found.append({"folder": child.name, "title": marker.title, "role": marker.role})
    return found
