"""The marker file that records whether a campaign folder is a master or a running copy."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MARKER_PATH = Path(".campaign") / "campaign.json"
FORMAT_VERSION = 1
ROLES = ("master", "running")


@dataclass
class CampaignMarker:
    role: str
    title: str
    created: str
    format_version: int = FORMAT_VERSION
    edition: str | None = None
    source_master: str | None = None
    source_commit: str | None = None
    group: str | None = None
    started: str | None = None
    # Keys written by later versions or other agents are kept as they are.
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = {key: value for key, value in asdict(self).items() if key != "extra"}
        data = {key: value for key, value in data.items() if value is not None}
        return {**self.extra, **data}


def marker_file(folder: Path) -> Path:
    return folder / MARKER_PATH


def read_marker(folder: Path) -> CampaignMarker | None:
    path = marker_file(folder)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"The campaign marker {MARKER_PATH} is not valid JSON.") from error
    if not isinstance(data, dict):
        raise ValueError(f"The campaign marker {MARKER_PATH} must be a JSON object.")
    if data.get("role") not in ROLES:
        raise ValueError(
            f"The campaign marker {MARKER_PATH} must set role to 'master' or 'running'."
        )
    if not isinstance(data.get("title"), str) or not isinstance(data.get("created"), str):
        raise ValueError(
            f"The campaign marker {MARKER_PATH} must include a title and created date."
        )
    known = set(CampaignMarker.__dataclass_fields__) - {"extra"}
    return CampaignMarker(
        **{key: value for key, value in data.items() if key in known},
        extra={key: value for key, value in data.items() if key not in known},
    )


def write_marker(folder: Path, marker: CampaignMarker) -> Path:
    path = marker_file(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(marker.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path
