from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_campaign.epic import check_epic, epic_summary, ordered_books
from ai_campaign.lifecycle import create_campaign, create_epic, start_campaign


def messages(epic: Path) -> list[tuple[str, str, str]]:
    return [(i.severity, i.file, i.message) for i in check_epic(epic)]


def list_books(epic: Path, *folders: str) -> None:
    text = (epic / "epic.md").read_text()
    books = "".join(
        f"{n}. [Book {n}]({folder}/campaign.md) - levels {n}-{n + 2}\n"
        for n, folder in enumerate(folders, start=1)
    )
    (epic / "epic.md").write_text(text.replace("## Books\n\n", f"## Books\n\n{books}\n"))


def npc(book: Path, name: str, status: str = "alive", index: str = "npcs.md") -> None:
    path = book / index
    path.write_text(
        path.read_text()
        + f"\n## {name}\n- **Appears in:** [Overview](campaign.md)\n- **Status:** {status}\n"
    )


@pytest.fixture
def saga(tmp_path: Path) -> Path:
    root = tmp_path / "saga"
    create_epic(root, "Saga")
    (root / "epic.md").write_text(
        (root / "epic.md")
        .read_text()
        .replace("## Story\n\n_To be written._", "## Story\n\nA road.")
    )
    create_campaign(root / "01-dawn", "Dawn")
    create_campaign(root / "02-dusk", "Dusk")
    list_books(root, "01-dawn", "02-dusk")
    return root


def epic_only(found: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """Drop each book's own campaign checks (a new book has no goal or adventure yet)."""
    return [m for m in found if not m[1].startswith(("01-", "02-", "03-"))]


def test_listed_books_in_order_have_no_epic_issues(saga: Path) -> None:
    assert epic_only(messages(saga)) == []
    assert [book.name for book in ordered_books(saga)] == ["01-dawn", "02-dusk"]


def test_book_list_problems(saga: Path) -> None:
    create_campaign(saga / "03-night", "Night")
    text = (saga / "epic.md").read_text()
    (saga / "epic.md").write_text(text.replace(
        "2. [Book 2](02-dusk/campaign.md)",
        "2. [Book 2](02-dusk/campaign.md)\n3. [Lost](99-lost/campaign.md)\n"
        "4. [Again](01-dawn/campaign.md)",
    ))
    found = messages(saga)
    assert ("error", "epic.md", (
        "Book link '99-lost/campaign.md' does not point to a book's "
            "campaign.md."
    )) in found
    assert ("warning", "epic.md", "'01-dawn' is listed more than once.") in found
    assert ("warning", "03-night", "Book 'Night' is not in the Books list in epic.md.") in found


def test_running_copies_are_not_books(saga: Path) -> None:
    start_campaign(saga / "01-dawn", "Tuesday")
    assert epic_only(messages(saga)) == []
    assert epic_summary(saga)["running_copies"] == ["01-dawn--tuesday"]


def test_rules_edition_must_match(saga: Path) -> None:
    create_campaign(saga / "03-odd", "Odd", rules="D&D 5e (2014)")
    found = messages(saga)
    assert ("warning", "03-odd/campaign.md", (
        "Uses D&D 5e (2014), but the epic uses "
            "D&D 5e (2024)."
    )) in found


def test_npc_who_dies_cannot_be_key_in_a_later_book(saga: Path) -> None:
    npc(saga / "01-dawn", "Hesk", "dies at Gallows Cross")
    npc(saga / "02-dusk", "Hesk")
    npc(saga / "01-dawn", "Ring of Ash", "destroyed in the forge", index="items.md")
    npc(saga / "02-dusk", "Ring of Ash", "worn by the villain", index="items.md")
    found = messages(saga)
    assert ("warning", "02-dusk/npcs.md", (
        "'Hesk' is a key entry here, but ends in Dawn "
            "(dies at Gallows Cross)."
    )) in found
    assert ("warning", "02-dusk/items.md", (
        "'Ring of Ash' is a key entry here, but ends in "
            "Dawn (destroyed in the forge)."
    )) in found


def test_book_order_follows_epic_md_not_folder_names(saga: Path) -> None:
    # Dusk is listed first, so Hesk dying in Dawn (book 2) does not affect Dusk (book 1).
    text = (saga / "epic.md").read_text()
    (saga / "epic.md").write_text(
        text.replace("1. [Book 1](01-dawn/", "1. [Book 1](02-dusk/", 1)
        .replace("2. [Book 2](02-dusk/", "2. [Book 2](01-dawn/", 1)
    )
    npc(saga / "01-dawn", "Hesk", "dies")
    npc(saga / "02-dusk", "Hesk")
    assert not any("ends in" in m for _, _, m in messages(saga))


def test_recurring_entries_belong_in_the_epic_index(saga: Path) -> None:
    npc(saga / "01-dawn", "Mara")
    npc(saga / "02-dusk", "Mara")
    assert ("warning", "npcs.md", (
        "'mara' appears in Dawn, Dusk but is not in the epic's "
            "index."
    )) in messages(saga)
    (saga / "npcs.md").write_text(
        (saga / "npcs.md").read_text()
        + "\n## Mara\n- **Books:** [Dawn](01-dawn/campaign.md)\n"
    )
    assert not any("Mara" in m or "mara" in m for _, f, m in messages(saga) if f == "npcs.md")


def test_epic_index_entries_must_link_to_a_book(saga: Path) -> None:
    (saga / "items.md").write_text(
        (saga / "items.md").read_text() + "\n## Crown\n- **Books:** none yet\n"
    )
    assert ("warning", "items.md", "Index entry 'Crown' does not link to any book.") in messages(
        saga
    )


def test_each_books_own_checks_are_included(saga: Path) -> None:
    found = messages(saga)
    assert ("warning", "01-dawn/campaign.md", "The campaign has no goal yet.") in found


def test_not_an_epic(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not an epic"):
        check_epic(tmp_path)


def test_epic_in_git_commits_books_separately(tmp_path: Path) -> None:
    root = tmp_path / "saga"
    create_epic(root, "Saga", init_git=True)
    create_campaign(root / "01-dawn", "Dawn")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    assert status == ""
