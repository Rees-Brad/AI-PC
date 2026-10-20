from __future__ import annotations

from pathlib import Path

import pytest

from ai_campaign.lifecycle import create_campaign


@pytest.fixture(autouse=True)
def git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let tests commit without depending on the machine's git configuration."""
    for prefix in ("GIT_AUTHOR", "GIT_COMMITTER"):
        monkeypatch.setenv(f"{prefix}_NAME", "Campaign Test")
        monkeypatch.setenv(f"{prefix}_EMAIL", "campaign-test@example.com")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def campaign(tmp_path: Path) -> Path:
    """A small, valid master campaign: one chapter, one adventure, one encounter, one map."""
    root = tmp_path / "sunken-crown"
    create_campaign(root, "The Sunken Crown")
    chapter = "chapters/01-the-drowned-coast"
    write(
        root / "campaign.md",
        "# The Sunken Crown\n\n## Goal\n\nRecover the crown before the tide turns.\n\n"
        "## Rules\n\nD&D 5e (2024).\n\n"
        f"## Chapters\n\n- [The Drowned Coast]({chapter}/chapter.md)\n\n"
        "![World](maps/world.png)\n",
    )
    write(
        root / chapter / "chapter.md",
        "# The Drowned Coast\n\n- [Smugglers' Cove](adventures/01-smugglers-cove.md)\n"
        "- [Harbor Brawl](encounters/01-harbor-brawl.md)\n",
    )
    write(
        root / chapter / "adventures/01-smugglers-cove.md",
        "# Smugglers' Cove\n\n![Cove](../../../maps/cove.png)\n",
    )
    write(root / chapter / "encounters/01-harbor-brawl.md", "# Harbor Brawl\n")
    for name in ("world.png", "cove.png"):
        (root / "maps" / name).write_bytes(b"\x89PNG\r\n")
    write(
        root / "npcs.md",
        "# Key NPCs\n\n## Captain Mara\n- **Appears in:** "
        f"[Smugglers' Cove]({chapter}/adventures/01-smugglers-cove.md)\n",
    )
    return root
