"""Read a campaign folder and check its structure, links, indexes, and maps."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import unquote

from ai_campaign.marker import MARKER_PATH, read_marker

CAMPAIGN_FILE = "campaign.md"
CHAPTER_FILE = "chapter.md"
CHAPTERS_DIR = "chapters"
MAPS_DIR = "maps"
SESSIONS_DIR = "sessions"
GETTING_STARTED_FILE = "GETTING_STARTED.md"
OPEN_ITEMS_FILE = "OPEN_ITEMS.md"
WORKLOG_FILE = "WORKLOG.md"
# The guide is generated and the work log is history, so their links are not checked.
UNCHECKED_FILES = {GETTING_STARTED_FILE, WORKLOG_FILE}
INDEX_FILES = {
    "npcs.md": "Key NPCs",
    "items.md": "Key items",
    "locations.md": "Key locations",
}
SUPPORTED_MAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
PLACEHOLDER = "_To be written._"

_NUMBER_PREFIX = re.compile(r"^(\d+)-.+")
_LINK = re.compile(r"(!?)\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
_CHECKBOX = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s")
_FIELD = re.compile(r"^\s*[-*+]\s+\*\*([^*:]+):?\*\*:?\s*(.*)$")
ENCOUNTER_SUMMARY = "Encounter summary"
ENCOUNTER_TRACKER = "Encounter tracker"


@dataclass
class Issue:
    severity: str  # "error" or "warning"
    file: str
    message: str
    line: int | None = None


@dataclass
class Chapter:
    folder: Path
    adventures: list[Path] = field(default_factory=list)
    encounters: list[Path] = field(default_factory=list)

    @property
    def chapter_file(self) -> Path:
        return self.folder / CHAPTER_FILE


@dataclass
class Link:
    source: Path
    line: int
    target: str
    resolved: Path | None  # None for anchors within the same file


def visible_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, text) for lines outside code blocks and HTML comments."""
    text = _HTML_COMMENT.sub(lambda match: "\n" * match.group(0).count("\n"), text)
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            if not fence:
                fence = stripped[:3]
            elif stripped.startswith(fence):
                fence = ""
            continue
        if not fence:
            yield number, _INLINE_CODE.sub("", line)


def extract_links(source: Path) -> list[Link]:
    links = []
    text = source.read_text(encoding="utf-8", errors="replace")
    for number, line in visible_lines(text):
        for match in _LINK.finditer(line):
            target = match.group(2).strip("<>")
            if _EXTERNAL.match(target):
                continue
            path_part = unquote(target.split("#", 1)[0])
            resolved = (source.parent / path_part).resolve() if path_part else None
            links.append(Link(source=source, line=number, target=target, resolved=resolved))
    return links


def number_prefix(path: Path) -> int | None:
    match = _NUMBER_PREFIX.match(path.stem if path.is_file() else path.name)
    return int(match.group(1)) if match else None


def _is_hidden(path: Path, root: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(root).parts)


def find_chapters(root: Path) -> list[Chapter]:
    chapters_dir = root / CHAPTERS_DIR
    if not chapters_dir.is_dir():
        return []
    chapters = []
    for folder in sorted(p for p in chapters_dir.iterdir() if p.is_dir() and not p.is_symlink()):
        if folder.name.startswith("."):
            continue
        chapter = Chapter(folder=folder)
        for kind in ("adventures", "encounters"):
            kind_dir = folder / kind
            if kind_dir.is_dir():
                files = sorted(p for p in kind_dir.glob("*.md") if p.is_file())
                getattr(chapter, kind).extend(files)
        chapters.append(chapter)
    return chapters


def markdown_files(root: Path) -> list[Path]:
    """Campaign Markdown files, excluding hidden folders and the Scribe's session summaries."""
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file()
        and not _is_hidden(path, root)
        and path.relative_to(root).parts[0] != SESSIONS_DIR
    )


def map_files(root: Path) -> list[Path]:
    maps_dir = root / MAPS_DIR
    if not maps_dir.is_dir():
        return []
    return sorted(
        path for path in maps_dir.rglob("*") if path.is_file() and not _is_hidden(path, root)
    )


def index_entries(path: Path) -> list[tuple[str, int, list[Link]]]:
    """Each `## ` heading in an index file, with the links found under it."""
    entries: list[tuple[str, int, list[Link]]] = []
    links_by_line = defaultdict(list)
    for link in extract_links(path):
        links_by_line[link.line].append(link)
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in visible_lines(text):
        if line.startswith("## "):
            entries.append((line[3:].strip(), number, list(links_by_line.get(number, []))))
        elif entries:
            entries[-1][2].extend(links_by_line.get(number, []))
    return entries


def index_fields(path: Path) -> list[tuple[str, int, dict[str, str]]]:
    """Each `## ` entry in an index file with its `- **Field:** value` lines."""
    entries: list[tuple[str, int, dict[str, str]]] = []
    for number, line in visible_lines(path.read_text(encoding="utf-8", errors="replace")):
        if line.startswith("## "):
            entries.append((line[3:].strip(), number, {}))
        elif entries:
            match = _FIELD.match(line)
            if match:
                entries[-1][2][match.group(1).strip().lower()] = match.group(2).strip()
    return entries


def _headings(path: Path) -> set[str]:
    return {
        line.lstrip("#").strip().lower()
        for _, line in visible_lines(path.read_text(encoding="utf-8", errors="replace"))
        if line.startswith("#")
    }


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _section_body(path: Path, heading: str) -> str | None:
    """The text under a `## heading`, or None when the heading is missing."""
    lines = list(visible_lines(path.read_text(encoding="utf-8", errors="replace")))
    body: list[str] | None = None
    for _, line in lines:
        if line.startswith("## "):
            if body is not None:
                break
            if line[3:].strip().lower() == heading.lower():
                body = []
        elif body is not None:
            body.append(line)
    return None if body is None else "\n".join(body).strip()


def check_campaign(root: Path) -> list[Issue]:
    """Report structure problems without changing anything. Errors come first."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"{root} is not a folder.")
    issues: list[Issue] = []

    def add(severity: str, path: Path, message: str, line: int | None = None) -> None:
        issues.append(Issue(severity, _rel(path, root), message, line))

    marker = read_marker(root)
    if marker is None:
        add("warning", root / MARKER_PATH, "No campaign marker found; this folder was not "
            "created with create_campaign.")

    campaign_file = root / CAMPAIGN_FILE
    if not campaign_file.is_file():
        add("error", campaign_file, "The campaign overview file is missing.")
    for name, title in INDEX_FILES.items():
        if not (root / name).is_file():
            add("warning", root / name, f"The {title} index is missing.")

    chapters = find_chapters(root)
    for chapter in chapters:
        if number_prefix(chapter.folder) is None:
            add("warning", chapter.folder, "Chapter folder has no number prefix, such as "
                "'01-'.")
        if not chapter.chapter_file.is_file():
            add("error", chapter.chapter_file, "The chapter outline file is missing.")
        for kind in ("adventures", "encounters"):
            seen: dict[int, Path] = {}
            for path in getattr(chapter, kind):
                number = number_prefix(path)
                if number is None:
                    add("warning", path, "File name has no number prefix, such as '01-'.")
                elif number in seen:
                    add("warning", path, f"Shares number {number:02d} with "
                        f"{seen[number].name}.")
                else:
                    seen[number] = path
    chapter_numbers: dict[int, Path] = {}
    for chapter in chapters:
        number = number_prefix(chapter.folder)
        if number is None:
            continue
        if number in chapter_numbers:
            add("warning", chapter.folder, f"Shares number {number:02d} with "
                f"{chapter_numbers[number].name}.")
        else:
            chapter_numbers[number] = chapter.folder

    links_from: dict[Path, set[Path]] = defaultdict(set)
    linked: set[Path] = set()
    for source in markdown_files(root):
        if source.parent == root and source.name in UNCHECKED_FILES:
            continue
        for link in extract_links(source):
            if link.resolved is None:
                continue
            if not link.resolved.is_relative_to(root):
                add("warning", source, f"Link to '{link.target}' points outside the campaign "
                    "folder.", link.line)
            elif not link.resolved.exists():
                add("error", source, f"Broken link to '{link.target}'.", link.line)
            else:
                links_from[source].add(link.resolved)
                linked.add(link.resolved)

    for path in map_files(root):
        if path.suffix.lower() not in SUPPORTED_MAP_SUFFIXES:
            add("warning", path, "Unsupported map format; use PNG, JPEG, or WebP.")
        if path not in linked:
            add("warning", path, "Map is not linked from any section.")

    for chapter in chapters:
        if chapter.chapter_file.is_file() and chapter.chapter_file not in links_from[
            campaign_file
        ]:
            add("warning", chapter.chapter_file, f"Chapter is not linked from {CAMPAIGN_FILE}.")
        for path in chapter.adventures + chapter.encounters:
            if path not in links_from[chapter.chapter_file]:
                add("warning", path, f"Not linked from its {CHAPTER_FILE}.")
        for path in chapter.encounters:
            headings = _headings(path)
            for heading in (ENCOUNTER_SUMMARY, ENCOUNTER_TRACKER):
                if heading.lower() not in headings:
                    add("warning", path, f"The encounter has no '## {heading}' section.")

    sections = {campaign_file} | {
        path
        for chapter in chapters
        for path in [chapter.chapter_file, *chapter.adventures, *chapter.encounters]
    }
    for name in INDEX_FILES:
        index_path = root / name
        if not index_path.is_file():
            continue
        for entry, line, links in index_entries(index_path):
            if not any(link.resolved in sections for link in links):
                add("warning", index_path, f"Index entry '{entry}' does not link to any "
                    "campaign section.", line)

    if campaign_file.is_file():
        goal = _section_body(campaign_file, "Goal")
        if not goal or goal == PLACEHOLDER:
            add("warning", campaign_file, "The campaign has no goal yet.")
        if not _section_body(campaign_file, "Rules"):
            add("warning", campaign_file, "The rules edition is not recorded; add a Rules "
                "section, such as 'D&D 5e (2024)'.")
    if not any(chapter.adventures for chapter in chapters):
        add("warning", root / CHAPTERS_DIR, "A campaign needs at least one adventure with at "
            "least one encounter.")

    return sorted(issues, key=lambda issue: issue.severity != "error")


def open_items(path: Path) -> dict[str, int] | None:
    """Count open and done checklist items, or None when the file is missing."""
    if not path.is_file():
        return None
    counts = {"open": 0, "done": 0}
    for _, line in visible_lines(path.read_text(encoding="utf-8", errors="replace")):
        match = _CHECKBOX.match(line)
        if match:
            counts["open" if match.group(1) == " " else "done"] += 1
    return counts


def campaign_summary(root: Path) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"{root} is not a folder.")
    marker = read_marker(root)
    sessions_dir = root / SESSIONS_DIR
    return {
        "folder": str(root),
        "is_campaign": marker is not None,
        "marker": marker.to_dict() if marker else None,
        "chapters": [
            {
                "folder": _rel(chapter.folder, root),
                "has_outline": chapter.chapter_file.is_file(),
                "adventures": [_rel(path, root) for path in chapter.adventures],
                "encounters": [_rel(path, root) for path in chapter.encounters],
            }
            for chapter in find_chapters(root)
        ],
        "maps": [_rel(path, root) for path in map_files(root)],
        "indexes": {
            name: len(index_entries(root / name)) if (root / name).is_file() else None
            for name in INDEX_FILES
        },
        "open_items": open_items(root / OPEN_ITEMS_FILE),
        "missing_agent_files": [
            name
            for name in (GETTING_STARTED_FILE, OPEN_ITEMS_FILE, WORKLOG_FILE)
            if not (root / name).is_file()
        ],
        "sessions": sorted(p.name for p in sessions_dir.glob("*.md")) if sessions_dir.is_dir()
        else [],
    }


def issues_as_dicts(issues: list[Issue]) -> list[dict[str, object]]:
    return [{k: v for k, v in asdict(issue).items() if v is not None} for issue in issues]
