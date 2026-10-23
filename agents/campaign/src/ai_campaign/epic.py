"""Checks across the books of an epic.

These are the structural checks: the book list, rules editions, links, and fates
recorded in the indexes. Story review (timeline, motivation, foreshadowing) is
done by the agent, which reads the books; see the check-epic skill.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ai_campaign import containers
from ai_campaign.marker import read_marker
from ai_campaign.structure import (
    CAMPAIGN_FILE,
    INDEX_FILES,
    PLACEHOLDER,
    Issue,
    _rel,
    _section_body,
    check_campaign,
    extract_links,
    index_fields,
    visible_lines,
)

EPIC_FILE = "epic.md"
_LIST_ITEM = re.compile(r"^\s*(\d+)[.)]\s+")
_ENDS = {
    "npcs.md": re.compile(r"\b(dies|died|dead|killed|slain|deceased|executed)\b", re.I),
    "items.md": re.compile(r"\b(destroyed|lost|consumed|shattered|unmade)\b", re.I),
    "locations.md": re.compile(r"\b(destroyed|razed|sunk|ruined|lost)\b", re.I),
}
_ENDING_FIELDS = ("status", "fate")


def books_on_disk(epic: Path) -> list[Path]:
    """Master campaigns directly inside the epic. Running copies are not books."""
    return [
        epic / member["folder"]
        for member in containers.members(epic)
        if member["role"] == "master"
    ]


def listed_books(epic: Path) -> list[tuple[int, str, Path | None]]:
    """(line, link target, resolved book folder) for each numbered item in ## Books."""
    path = epic / EPIC_FILE
    if not path.is_file():
        return []
    lines = list(visible_lines(path.read_text(encoding="utf-8", errors="replace")))
    in_books = False
    numbered = set()
    for number, line in lines:
        if line.startswith("## "):
            in_books = line[3:].strip().lower() == "books"
        elif in_books and _LIST_ITEM.match(line):
            numbered.add(number)
    found = []
    for link in extract_links(path):
        if link.line in numbered and link.resolved is not None:
            folder = link.resolved.parent if link.resolved.name == CAMPAIGN_FILE else None
            found.append((link.line, link.target, folder))
    return found


def ordered_books(epic: Path) -> list[Path]:
    """Books in the epic's reading order, then any not yet listed, by folder name."""
    on_disk = books_on_disk(epic)
    ordered = []
    for _, _, folder in listed_books(epic):
        if folder in on_disk and folder not in ordered:
            ordered.append(folder)
    return ordered + [book for book in on_disk if book not in ordered]


def _title(book: Path) -> str:
    marker = read_marker(book)
    return marker.title if marker else book.name


def check_epic(epic: Path) -> list[Issue]:
    """Structural checks across an epic's books, plus each book's own checks."""
    epic = epic.resolve()
    container = containers.read_container(epic)
    if container is None or container["kind"] != containers.EPIC:
        raise ValueError(f"{epic} is not an epic; it has no epic marker.")
    issues: list[Issue] = []

    def add(severity: str, path: Path, message: str, line: int | None = None) -> None:
        issues.append(Issue(severity, _rel(path, epic), message, line))

    epic_file = epic / EPIC_FILE
    if not epic_file.is_file():
        add("error", epic_file, "The epic's overview file is missing.")
    else:
        story = _section_body(epic_file, "Story")
        if not story or story == PLACEHOLDER:
            add("warning", epic_file, "The epic has no story yet.")

    # The book list
    on_disk = books_on_disk(epic)
    seen: set[Path] = set()
    for line, target, folder in listed_books(epic):
        if folder is None or not (folder / CAMPAIGN_FILE).is_file():
            add("error", epic_file, f"Book link '{target}' does not point to a book's "
                f"{CAMPAIGN_FILE}.", line)
        elif folder not in on_disk:
            add("warning", epic_file, f"'{folder.name}' is listed as a book but is not a "
                "master campaign.", line)
        elif folder in seen:
            add("warning", epic_file, f"'{folder.name}' is listed more than once.", line)
        if folder is not None:
            seen.add(folder)
    for book in on_disk:
        if book not in seen:
            add("warning", book, f"Book '{_title(book)}' is not in the Books list in "
                f"{EPIC_FILE}.")
    if not on_disk:
        add("warning", epic, "The epic has no books yet.")

    # Rules editions
    epic_rules = container.get("rules")
    for book in on_disk:
        marker = read_marker(book)
        book_rules = marker.rules if marker else None
        if epic_rules and book_rules and book_rules != epic_rules:
            add("warning", book / CAMPAIGN_FILE, f"Uses {book_rules}, but the epic uses "
                f"{epic_rules}.")

    # Links in the epic's own files
    for source in sorted(epic.glob("*.md")):
        if source.name == "GETTING_STARTED.md" or source.name == "WORKLOG.md":
            continue
        for link in extract_links(source):
            if link.resolved is None:
                continue
            if not link.resolved.is_relative_to(epic):
                add("warning", source, f"Link to '{link.target}' points outside the epic.",
                    link.line)
            elif not link.resolved.exists():
                add("error", source, f"Broken link to '{link.target}'.", link.line)

    # Epic index entries should point into at least one book
    for name in INDEX_FILES:
        index = epic / name
        if not index.is_file():
            add("warning", index, f"The epic's {INDEX_FILES[name]} index is missing.")
            continue
        names = defaultdict(list)
        for entry, line, _ in index_fields(index):
            names[entry.casefold()].append(line)
        for entry_links in _entry_links(index):
            entry, line, targets = entry_links
            if not any(any(t.is_relative_to(book) for book in on_disk) for t in targets):
                add("warning", index, f"Index entry '{entry}' does not link to any book.", line)
        for entry, lines in names.items():
            if len(lines) > 1:
                add("warning", index, f"'{entry}' has more than one entry.", lines[1])

    # Fates across books, in reading order
    books = ordered_books(epic)
    for name, pattern in _ENDS.items():
        ended: dict[str, Path] = {}
        appears: dict[str, list[Path]] = defaultdict(list)
        epic_entries = (
            {e.casefold() for e, _, _ in index_fields(epic / name)}
            if (epic / name).is_file()
            else set()
        )
        for book in books:
            index = book / name
            if not index.is_file():
                continue
            seen_here: dict[str, int] = {}
            for entry, line, fields in index_fields(index):
                key = entry.casefold()
                if key in seen_here:
                    add("warning", index, f"'{entry}' has more than one entry.", line)
                    continue
                seen_here[key] = line
                if key in ended:
                    add("warning", index, f"'{entry}' is a key entry here, but ends in "
                        f"{_title(ended[key])} ({_ending(ended[key] / name, key)}).", line)
                appears[key].append(book)
                if any(pattern.search(fields.get(field, "")) for field in _ENDING_FIELDS):
                    ended.setdefault(key, book)
        for key, in_books in appears.items():
            if len(in_books) > 1 and key not in epic_entries:
                titles = ", ".join(_title(book) for book in in_books)
                add("warning", epic / name, f"'{key}' appears in {titles} but is not in the "
                    "epic's index.")

    # Each book's own checks
    for book in on_disk:
        for issue in check_campaign(book):
            issues.append(
                Issue(issue.severity, f"{book.name}/{issue.file}", issue.message, issue.line)
            )

    return sorted(issues, key=lambda issue: issue.severity != "error")


def _entry_links(index: Path) -> list[tuple[str, int, list[Path]]]:
    """Each entry in an index with the resolved targets of its links."""
    entries: list[tuple[str, int, list[Path]]] = []
    links_by_line = defaultdict(list)
    for link in extract_links(index):
        if link.resolved is not None:
            links_by_line[link.line].append(link.resolved)
    for number, line in visible_lines(index.read_text(encoding="utf-8", errors="replace")):
        if line.startswith("## "):
            entries.append((line[3:].strip(), number, list(links_by_line.get(number, []))))
        elif entries:
            entries[-1][2].extend(links_by_line.get(number, []))
    return entries


def _ending(index: Path, key: str) -> str:
    for entry, _, fields in index_fields(index):
        if entry.casefold() == key:
            return next(
                (fields[f] for f in _ENDING_FIELDS if fields.get(f)), "ends"
            )
    return "ends"


def epic_summary(epic: Path) -> dict[str, object]:
    epic = epic.resolve()
    return {
        "books_in_order": [
            {"folder": book.name, "title": _title(book), "listed": book in {
                folder for _, _, folder in listed_books(epic)
            }}
            for book in ordered_books(epic)
        ],
        "running_copies": [
            m["folder"] for m in containers.members(epic) if m["role"] == "running"
        ],
    }
