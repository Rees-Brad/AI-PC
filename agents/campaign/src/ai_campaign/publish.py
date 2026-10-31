"""Publish a master campaign as a PDF (Release 2, digital output).

The PDF follows the campaign's structure: title page, copyright page, contents,
the overview, each chapter with its adventures and encounters, then the indexes
as appendices. An epic is published as one PDF per book. Publishing reads the
campaign and writes only to the output folder; publishing details (author,
copyright) are kept in `.campaign/publish.json` by `set_publish_details`.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

import markdown
from markdown.extensions.toc import TocExtension
from markdown.treeprocessors import Treeprocessor
from weasyprint import HTML
from weasyprint.urls import URLFetcher

from ai_campaign import containers, epic, systems
from ai_campaign.marker import read_marker, write_marker
from ai_campaign.structure import (
    CAMPAIGN_FILE,
    INDEX_FILES,
    MAPS_DIR,
    PLACEHOLDER,
    SUPPORTED_MAP_SUFFIXES,
    Issue,
    _rel,
    check_campaign,
    find_chapters,
    visible_lines,
)

PUBLISH_FILE = Path(".campaign") / "publish.json"
OUTPUT_DIR = "published"
PAGE_SIZES = {"letter": "Letter", "a4": "A4"}
DETAIL_KEYS = (
    "author",
    "credits",
    "cover_image",
    "copyright_holder",
    "copyright_year",
    "rights",
    "license_text",
    "footer_notice",
    "page_size",
    "map_appendix",
)
DEFAULT_DETAILS: dict[str, Any] = {
    "rights": "All rights reserved.",
    "footer_notice": False,
    "page_size": "Letter",
    "map_appendix": False,
}
TRACKER_HEADING = "encounter tracker"
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


# Publishing details

def read_details(folder: Path) -> dict[str, Any]:
    """Publishing details for a campaign, a book inheriting from its epic's."""
    details = dict(DEFAULT_DETAILS)
    container = containers.find_container(folder)
    sources = [folder]
    if container is not None and container["kind"] == containers.EPIC:
        sources.insert(0, Path(container["folder"]))
    for source in sources:
        path = source / PUBLISH_FILE
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                raise ValueError(f"{PUBLISH_FILE} in {source} is not valid JSON.") from error
            details.update({k: v for k, v in data.items() if k in DETAIL_KEYS})
            if "cover_image" in data:
                details["cover_base"] = str(source)
    return details


def set_publish_details(folder: Path, edition: str | None = None, **values: Any) -> dict[str, Any]:
    """Save publishing details for a master campaign or an epic. None leaves a value as is.

    The edition is stored in the campaign marker (or the epic marker); the other
    details in `.campaign/publish.json`, where every later edition reuses them.
    """
    folder = folder.resolve()
    marker = read_marker(folder)
    container = containers.read_container(folder)
    if marker is None and (container is None or container["kind"] != containers.EPIC):
        raise ValueError(f"{folder} is not a campaign or an epic.")
    if marker is not None and marker.role != "master":
        raise ValueError("Publishing details belong to the master campaign, not a running copy.")
    unknown = set(values) - set(DETAIL_KEYS)
    if unknown:
        raise ValueError(f"Unknown publishing details: {', '.join(sorted(unknown))}.")
    if values.get("page_size") is not None:
        values["page_size"] = _page_size(values["page_size"])
    if values.get("cover_image") and not (folder / values["cover_image"]).is_file():
        raise ValueError(f"Cover image '{values['cover_image']}' was not found in {folder}.")

    path = folder / PUBLISH_FILE
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    data.update({k: v for k, v in values.items() if v is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    if edition is not None:
        if marker is not None:
            marker.edition = edition
            write_marker(folder, marker)
        else:
            stored = {k: v for k, v in (container or {}).items() if k not in ("kind", "folder")}
            containers.write_container(folder, containers.EPIC, {**stored, "edition": edition})
    return {
        "folder": str(folder),
        "details": {k: v for k, v in data.items() if k in DETAIL_KEYS},
        "edition": edition if edition is not None else _edition(folder),
    }


def _page_size(value: str) -> str:
    size = PAGE_SIZES.get(str(value).strip().lower())
    if size is None:
        raise ValueError("Page size must be Letter or A4.")
    return size


def _edition(folder: Path) -> str | None:
    marker = read_marker(folder)
    if marker is not None and marker.edition:
        return marker.edition
    container = containers.find_container(folder) if marker else containers.read_container(folder)
    if container is not None and container["kind"] == containers.EPIC:
        return container.get("edition")
    return None


# What goes in the book

@dataclass
class Section:
    path: Path
    kind: str  # overview, chapter, adventure, encounter, index
    level: int  # bookmark level of the section's title


def book_sections(root: Path) -> list[Section]:
    """The campaign's sections in book order. Working documents are left out."""
    sections = []
    if (root / CAMPAIGN_FILE).is_file():
        sections.append(Section(root / CAMPAIGN_FILE, "overview", 1))
    for chapter in find_chapters(root):
        if chapter.chapter_file.is_file():
            sections.append(Section(chapter.chapter_file, "chapter", 1))
        sections += [Section(path, "adventure", 2) for path in chapter.adventures]
        sections += [Section(path, "encounter", 2) for path in chapter.encounters]
    sections += [
        Section(root / name, "index", 1) for name in INDEX_FILES if (root / name).is_file()
    ]
    return sections


# Readiness

def readiness(folder: Path) -> list[Issue]:
    """Everything worth fixing before publishing: the structure checks, plus placeholder
    and empty sections, adventures with no map, and missing publishing details."""
    folder = folder.resolve()
    container = containers.read_container(folder)
    if container is not None and container["kind"] == containers.EPIC:
        issues = epic.check_epic(folder)
        for book in epic.ordered_books(folder):
            issues += [
                Issue(i.severity, f"{book.name}/{i.file}", i.message, i.line)
                for i in _content_issues(book)
            ]
        issues += _detail_issues(folder, folder)
    else:
        marker = read_marker(folder)
        if marker is None:
            raise ValueError(f"{folder} is not a campaign or an epic.")
        if marker.role != "master":
            return [Issue("error", ".campaign/campaign.json", "This is a running copy. Only "
                          "master campaigns are published.")]
        issues = check_campaign(folder) + _content_issues(folder) + _detail_issues(folder, folder)
    return sorted(issues, key=lambda issue: issue.severity != "error")


def _content_issues(root: Path) -> list[Issue]:
    issues = []
    for section in book_sections(root):
        rel = _rel(section.path, root)
        lines = list(visible_lines(section.path.read_text(encoding="utf-8", errors="replace")))
        for number, line in lines:
            if PLACEHOLDER in line:
                issues.append(Issue("warning", rel, "Placeholder text: not written yet.", number))
        for number, heading in _empty_headings(lines):
            issues.append(Issue("warning", rel, f"The '{heading}' section is empty.", number))
        if section.kind == "adventure" and not any(
            _is_map_link(section.path, root, line) for _, line in lines
        ):
            issues.append(Issue("warning", rel, "The adventure has no map. Fine if none is "
                                "needed."))
    return issues


def _empty_headings(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Headings with nothing under them before the next heading of the same or higher level."""
    empty = []
    for i, (number, line) in enumerate(lines):
        match = _HEADING.match(line)
        if not match:
            continue
        level = len(match.group(1))
        for _, after in lines[i + 1:]:
            following = _HEADING.match(after)
            if following and len(following.group(1)) <= level:
                empty.append((number, match.group(2)))
                break
            if after.strip():
                break
        else:
            empty.append((number, match.group(2)))
    return empty


def _is_map_link(source: Path, root: Path, line: str) -> bool:
    for target in re.findall(r"\]\(\s*<?([^)>\s]+)", line):
        if not _EXTERNAL.match(target):
            path = (source.parent / unquote(target.split("#", 1)[0])).resolve()
            if path.is_relative_to(root / MAPS_DIR):
                return True
    return False


def _detail_issues(folder: Path, root: Path) -> list[Issue]:
    details = read_details(folder)
    issues = []
    rel = PUBLISH_FILE.as_posix()
    if not details.get("author"):
        issues.append(Issue("warning", rel, "No author name for the title page."))
    if not details.get("copyright_holder"):
        issues.append(Issue("warning", rel, "No copyright holder for the copyright page."))
    if not _edition(folder):
        issues.append(Issue("warning", rel, "No edition recorded, such as '1.0'."))
    cover = details.get("cover_image")
    if cover and not (Path(details["cover_base"]) / cover).is_file():
        issues.append(Issue("error", rel, f"Cover image '{cover}' is missing."))
    if _rules(folder) and systems.rules_family(_rules(folder)) == systems.DND_3_5 and (
        "open game license" not in str(details.get("license_text") or "").lower()
    ):
        issues.append(Issue("warning", rel, "D&D 3.5 material is Open Game Content under the "
                            "Open Game License 1.0a. Add the full license text and its Section "
                            "15 notice to the license text, and say which material is Open Game "
                            "Content."))
    return issues


def _rules(folder: Path) -> str | None:
    marker = read_marker(folder)
    if marker is not None:
        return marker.rules
    container = containers.read_container(folder)
    return container.get("rules") if container else None


# Rendering

@dataclass
class _Book:
    """State shared while rendering one book's sections."""

    root: Path
    section_ids: dict[Path, str]
    shown_maps: dict[Path, str] = field(default_factory=dict)  # map -> figure id
    linked_maps: set[Path] = field(default_factory=set)
    trackers: int = 0


def _slug(value: str, separator: str = "-") -> str:
    """GitHub-style heading anchors, so links like `file.md#heading` keep working."""
    value = re.sub(r"[^\w\- ]", "", value.strip().lower())
    return re.sub(r"\s", separator, value)


def section_id(root: Path, path: Path) -> str:
    return "s-" + _slug(_rel(path, root).removesuffix(".md").replace("/", " "))


def map_id(root: Path, path: Path) -> str:
    return "map-" + _slug(_rel(path, root / MAPS_DIR).replace("/", " ").replace(".", " "))


class _Rewriter(Treeprocessor):
    """Makes a section's ids unique in the book and points its links inside the PDF."""

    def __init__(self, md: markdown.Markdown, book: _Book, section: Section) -> None:
        super().__init__(md)
        self.book = book
        self.section = section
        self.prefix = book.section_ids[section.path]

    def run(self, root: ET.Element) -> None:
        shift = 1 if self.section.kind in ("adventure", "encounter") else 0
        titled = False
        for element in root.iter():
            if element.get("id"):
                element.set("id", f"{self.prefix}--{element.get('id')}")
            if re.fullmatch(r"h[1-6]", element.tag):
                level = min(int(element.tag[1]) + shift, 6)
                element.tag = f"h{level}"
                if not titled and level == 1 + shift:
                    element.set("class", f"title bm{self.section.level}")
                    titled = True
        for parent, child in [(parent, child) for parent in root.iter() for child in parent]:
            if child.tag == "a" and child.get("href") is not None:
                self._link(child)
            elif child.tag == "img":
                replacement = self._image(child, parent)
                index = list(parent).index(child)
                parent.remove(child)
                parent.insert(index, replacement)
        self._wrap_trackers(root)

    def _resolve(self, target: str) -> tuple[Path | None, str]:
        path_part, _, anchor = target.partition("#")
        if not path_part:
            return None, anchor
        return (self.section.path.parent / unquote(path_part)).resolve(), anchor

    def _link(self, element: ET.Element) -> None:
        target = element.get("href", "")
        if _EXTERNAL.match(target):
            return
        path, anchor = self._resolve(target)
        if path is None:
            element.set("href", f"#{self.prefix}--{anchor}" if anchor else f"#{self.prefix}")
        elif path in self.book.section_ids:
            sid = self.book.section_ids[path]
            element.set("href", f"#{sid}--{anchor}" if anchor else f"#{sid}")
        elif path.is_file() and path.is_relative_to(self.book.root / MAPS_DIR):
            self.book.linked_maps.add(path)
            element.set("href", f"#{map_id(self.book.root, path)}")
        else:
            # Working documents, session notes, and anything outside the book.
            element.tag = "span"
            del element.attrib["href"]

    def _image(self, element: ET.Element, parent: ET.Element) -> ET.Element:
        path, _ = self._resolve(element.get("src", ""))
        alt = element.get("alt") or "Map"
        if path is None or _EXTERNAL.match(element.get("src", "")):
            return _text_element("span", f"[Image not included: {alt}]", "missing")
        if not path.is_file() or not path.is_relative_to(self.book.root):
            return _text_element("span", f"[Missing image: {alt}]", "missing")
        if path.suffix.lower() not in SUPPORTED_MAP_SUFFIXES:
            return _text_element("span", f"[Unsupported image format: {alt}]", "missing")
        if path in self.book.shown_maps:
            ref = _text_element("a", f"Map: {alt}", "map-ref")
            ref.set("href", f"#{self.book.shown_maps[path]}")
            return ref
        figure_id = map_id(self.book.root, path)
        self.book.shown_maps[path] = figure_id
        figure = ET.Element("figure", {"class": "map", "id": figure_id})
        ET.SubElement(figure, "img", {"src": path.as_uri(), "alt": alt})
        ET.SubElement(figure, "figcaption").text = alt
        if parent.tag == "p" and len(parent) == 1 and not (parent.text or "").strip():
            parent.tag = "div"
        return figure

    def _wrap_trackers(self, root: ET.Element) -> None:
        children = list(root)
        result: list[ET.Element] = []
        tracker: ET.Element | None = None
        tracker_level = 0
        for child in children:
            level = int(child.tag[1]) if re.fullmatch(r"h[1-6]", child.tag) else 0
            if tracker is not None and level and level <= tracker_level:
                tracker = None
            if level and "".join(child.itertext()).strip().lower() == TRACKER_HEADING:
                tracker = ET.Element("div", {"class": "tracker"})
                tracker_level = level
                result.append(tracker)
                self.book.trackers += 1
            if tracker is not None:
                tracker.append(child)
            else:
                result.append(child)
        for child in children:
            root.remove(child)
        root.extend(result)


def _text_element(tag: str, text: str, css_class: str) -> ET.Element:
    element = ET.Element(tag, {"class": css_class})
    element.text = text
    return element


def _render_section(book: _Book, section: Section) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", TocExtension(slugify=_slug)]
    )
    md.treeprocessors.register(_Rewriter(md, book, section), "campaign-links", 1)
    body = md.convert(section.path.read_text(encoding="utf-8", errors="replace"))
    sid = book.section_ids[section.path]
    if 'class="title' not in body:
        tag = "h2" if section.kind in ("adventure", "encounter") else "h1"
        title = section.path.stem.split("-", 1)[-1].replace("-", " ").title()
        body = f'<{tag} class="title bm{section.level}">{html.escape(title)}</{tag}>\n{body}'
    return f'<section id="{sid}" class="part {section.kind}">\n{body}\n</section>'


def _section_title(path: Path) -> str:
    for _, line in visible_lines(path.read_text(encoding="utf-8", errors="replace")):
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.split("-", 1)[-1].replace("-", " ").title()


def _md_inline(text: str) -> str:
    return markdown.markdown(text, extensions=["sane_lists"])


def _css_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def _stylesheet(page_size: str, footer: str | None) -> str:
    footer_rule = f"@bottom-left {{ content: {_css_string(footer)}; }}" if footer else ""
    return STYLESHEET.replace("PAGE_SIZE", page_size).replace("FOOTER_RULE", footer_rule)


STYLESHEET = """
@page { size: PAGE_SIZE; margin: 0.8in 0.75in 0.9in 0.75in;
  @bottom-right { content: counter(page); font-size: 9pt; color: #555; }
  FOOTER_RULE
}
@page front { @bottom-right { content: none; } @bottom-left { content: none; } }
@page tracker { margin: 0.6in; }
html { font-family: "DejaVu Serif", Georgia, serif; font-size: 10.5pt; line-height: 1.4;
  color: #111; }
@page :first { @bottom-right { content: none; } @bottom-left { content: none; } }
h1, h2, h3, h4, h5, h6 { font-family: "DejaVu Sans", Helvetica, sans-serif;
  bookmark-level: none; break-after: avoid; line-height: 1.2; }
h1 { font-size: 22pt; margin: 0 0 0.6em; }
h2 { font-size: 15pt; margin: 1.2em 0 0.4em; }
h3 { font-size: 12.5pt; margin: 1em 0 0.3em; }
h4, h5, h6 { font-size: 11pt; }
.bm1 { bookmark-level: 1; }
.bm2 { bookmark-level: 2; }
.part.overview, .part.chapter, .part.index { break-before: page; }
.part.adventure, .part.encounter { break-before: page; }
.part.index > h1.title::before { content: "Appendix: "; }
.part > h2.title { font-size: 18pt; margin-top: 0; }
.front { page: front; break-after: page; }
.title-page { text-align: center; padding-top: 2in; }
.title-page h1 { font-size: 32pt; }
.title-page .cover { max-width: 100%; max-height: 5in; margin: 0.4in auto; display: block; }
.title-page .series, .title-page .edition, .title-page .author { font-size: 13pt; margin: 0.3em; }
.copyright-page { padding-top: 5in; font-size: 9.5pt; }
nav.toc h1 { bookmark-level: 1; }
nav.toc ol { list-style: none; padding: 0; }
nav.toc li.l2 { padding-left: 1.5em; }
nav.toc a { color: inherit; text-decoration: none; }
nav.toc a::after { content: leader('.') target-counter(attr(href), page); }
a { color: #1a4c8b; text-decoration: none; }
a.map-ref::after { content: " (page " target-counter(attr(href), page) ")"; }
table { border-collapse: collapse; width: 100%; margin: 0.6em 0; break-inside: auto; }
th, td { border: 0.6pt solid #888; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eee; }
figure.map { margin: 0.8em 0; break-inside: avoid; text-align: center; }
figure.map img { max-width: 100%; max-height: 7.5in; }
figcaption { font-size: 9pt; font-style: italic; margin-top: 0.3em; }
.tracker { page: tracker; break-before: page; break-after: page; }
.tracker td { height: 2.4em; }
.missing { color: #a00; font-style: italic; }
.appendix-maps figure.map + figure.map { break-before: page; }
.appendix-maps figure.map img { max-height: 8.5in; }
pre, code { font-family: "DejaVu Sans Mono", monospace; font-size: 9pt; }
blockquote { margin: 0.6em 1.2em; padding-left: 0.8em; border-left: 2pt solid #bbb;
  font-style: italic; }
"""


class _LocalFetcher(URLFetcher):
    """Load only files inside the allowed folders; never fetch from the network."""

    def __init__(self, allowed: list[Path]) -> None:
        super().__init__(allowed_protocols=("file", "data"))
        self.allowed = [path.resolve() for path in allowed]

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> Any:
        if url.startswith("file:"):
            path = Path(url2pathname(urlsplit(url).path)).resolve()
            if not any(path.is_relative_to(root) for root in self.allowed):
                raise ValueError(f"Not loading {path}: it is outside the campaign.")
        return super().fetch(url, headers)


def render_book(
    root: Path,
    details: dict[str, Any],
    edition: str | None,
    series: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """The book's HTML, and counts for the report."""
    marker = read_marker(root)
    title = marker.title if marker else root.name
    sections = book_sections(root)
    book = _Book(root=root, section_ids={s.path: section_id(root, s.path) for s in sections})
    bodies = [_render_section(book, section) for section in sections]

    # Maps that were only linked, or all maps in an appendix when the author asks for one
    appendix_maps = [
        path for path in sorted(book.linked_maps) if path not in book.shown_maps
    ]
    if details.get("map_appendix"):
        appendix_maps = sorted(set(book.shown_maps) | set(book.linked_maps))
    if appendix_maps:
        figures = []
        for path in appendix_maps:
            figure_id = (
                f"full-{book.shown_maps[path]}" if path in book.shown_maps
                else map_id(root, path)
            )
            name = path.stem.replace("-", " ").replace("_", " ").title()
            if path.suffix.lower() in SUPPORTED_MAP_SUFFIXES:
                figures.append(
                    f'<figure class="map" id="{figure_id}"><img src="{path.as_uri()}" '
                    f'alt="{html.escape(name)}"><figcaption>{html.escape(name)}</figcaption>'
                    "</figure>"
                )
        bodies.append(
            '<section id="s-maps" class="part index appendix-maps">'
            '<h1 class="title bm1">Maps</h1>' + "".join(figures) + "</section>"
        )

    year = details.get("copyright_year") or date.today().year
    holder = details.get("copyright_holder")
    notice = f"© {year} {holder}. {details.get('rights') or ''}".strip() if holder else None
    author = details.get("author")

    front = ['<section class="front title-page">', f"<h1>{html.escape(title)}</h1>"]
    if series:
        front.append(f'<p class="series">{html.escape(series)}</p>')
    cover = details.get("cover_image")
    if cover and (Path(details["cover_base"]) / cover).is_file():
        front.append(
            f'<img class="cover" src="{(Path(details["cover_base"]) / cover).as_uri()}" alt="">'
        )
    if author:
        front.append(f'<p class="author">{html.escape(author)}</p>')
    if edition:
        front.append(f'<p class="edition">Edition {html.escape(edition)}</p>')
    front.append("</section>")

    front.append('<section class="front copyright-page">')
    front.append(f"<p><strong>{html.escape(title)}</strong></p>")
    if edition:
        front.append(f"<p>Edition {html.escape(edition)}</p>")
    if marker and marker.rules:
        front.append(f"<p>Rules: {html.escape(marker.rules)}</p>")
    if notice:
        front.append(f"<p>{html.escape(notice)}</p>")
    if details.get("license_text"):
        front.append(_md_inline(details["license_text"]))
    if details.get("credits"):
        front.append(_md_inline(details["credits"]))
    front.append("</section>")

    toc = ['<nav class="front toc"><h1>Contents</h1><ol>']
    for section in sections:
        toc.append(
            f'<li class="l{section.level}"><a href="#{book.section_ids[section.path]}">'
            f"{html.escape(_toc_label(section))}</a></li>"
        )
    if appendix_maps:
        toc.append('<li class="l1"><a href="#s-maps">Appendix: Maps</a></li>')
    toc.append("</ol></nav>")

    meta = {"author": author, "copyright": notice, "rights": details.get("rights"),
            "edition": edition, "rules": marker.rules if marker else None,
            "dcterms.created": date.today().isoformat()}
    head = [f"<title>{html.escape(title)}</title>"] + [
        f'<meta name="{name}" content="{html.escape(str(value))}">'
        for name, value in meta.items() if value
    ]
    footer = notice if details.get("footer_notice") else None
    document = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        + "".join(head)
        + f"<style>{_stylesheet(details.get('page_size') or 'Letter', footer)}</style></head>"
        + "<body>" + "".join(front) + "".join(toc) + "\n".join(bodies) + "</body></html>"
    )
    counts = {
        "sections": len(sections),
        "maps": len(set(book.shown_maps) | set(appendix_maps)),
        "encounter_trackers": book.trackers,
    }
    return document, counts


def _toc_label(section: Section) -> str:
    title = _section_title(section.path)
    return f"Appendix: {title}" if section.kind == "index" else title


def _output_name(title: str, edition: str | None, page_size: str, number: int | None) -> str:
    parts = [f"{number:02d}"] if number is not None else []
    parts.append(_slug(title) or "campaign")
    if edition:
        parts.append(_slug(edition.replace(".", "-")))
    parts.append(page_size.lower())
    return "-".join(parts) + ".pdf"


def publish(
    folder: Path,
    page_size: str | None = None,
    output_folder: Path | None = None,
    map_appendix: bool | None = None,
) -> dict[str, Any]:
    """Write the digital PDF of a master campaign, or one PDF per book of an epic."""
    folder = folder.resolve()
    container = containers.read_container(folder)
    is_epic = container is not None and container["kind"] == containers.EPIC
    if is_epic:
        books = epic.ordered_books(folder)
        if not books:
            raise ValueError("The epic has no books to publish.")
    else:
        marker = read_marker(folder)
        if marker is None:
            raise ValueError(f"{folder} is not a campaign or an epic.")
        if marker.role != "master":
            raise ValueError(
                "This is a running copy, which holds play history. Only master campaigns are "
                f"published; publish its master instead ({marker.source_master or 'unknown'})."
            )
        books = [folder]

    output = (output_folder or folder / OUTPUT_DIR).resolve()
    if output == folder or any(output == book for book in books):
        raise ValueError("Choose an output folder other than the campaign itself.")
    output.mkdir(parents=True, exist_ok=True)

    written = []
    for number, book in enumerate(books, start=1):
        details = read_details(book)
        if page_size is not None:
            details["page_size"] = _page_size(page_size)
        if map_appendix is not None:
            details["map_appendix"] = map_appendix
        edition = _edition(book)
        marker = read_marker(book)
        title = marker.title if marker else book.name
        series = f"Book {number} of {container['title']}" if is_epic and container else None
        document, counts = render_book(book, details, edition, series)
        allowed = [folder] + ([Path(details["cover_base"])] if details.get("cover_base") else [])
        rendered = HTML(
            string=document, base_url=str(book), url_fetcher=_LocalFetcher(allowed)
        ).render()
        target = output / _output_name(
            title, edition, details["page_size"], number if is_epic else None
        )
        rendered.write_pdf(target, custom_metadata=True)
        written.append({
            "pdf": str(target),
            "book": title,
            "pages": len(rendered.pages),
            "edition": edition,
            "page_size": details["page_size"],
            **counts,
        })

    result: dict[str, Any] = {"output_folder": str(output), "files": written}
    if output.is_relative_to(folder) and not _ignored(folder, output):
        result["note"] = (
            f"{_rel(output, folder)}/ is inside the campaign and not in .gitignore, so a "
            "snapshot would commit the PDFs. Offer to add it to .gitignore."
        )
    return result


def _ignored(folder: Path, output: Path) -> bool:
    gitignore = folder / ".gitignore"
    if not gitignore.is_file():
        return False
    name = _rel(output, folder).strip("/")
    lines = gitignore.read_text(encoding="utf-8").splitlines()
    entries = {line.strip().strip("/") for line in lines}
    return name in entries
