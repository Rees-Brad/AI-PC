from __future__ import annotations

import json
import struct
import subprocess
import zlib
from pathlib import Path

import pypdf
import pytest

from ai_campaign import publish
from ai_campaign.lifecycle import create_campaign, create_epic, start_campaign


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def png(path: Path, width: int = 40, height: int = 30) -> None:
    """A small, valid PNG, so the PDF renderer can place it."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(
            ">I", zlib.crc32(kind + data)
        )

    raw = b"".join(b"\x00" + b"\x50\x80\xc0" * width for _ in range(height))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


@pytest.fixture
def book(campaign: Path) -> Path:
    for name in ("world.png", "cove.png"):
        png(campaign / "maps" / name)
    return campaign


def outline(reader: pypdf.PdfReader) -> list[str]:
    titles: list[str] = []

    def walk(items: list) -> None:  # type: ignore[type-arg]
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                titles.append(item.title)

    walk(reader.outline)
    return titles


def text(reader: pypdf.PdfReader) -> str:
    return "\n".join(page.extract_text() for page in reader.pages)


def test_book_sections_follow_the_campaign_structure(book: Path) -> None:
    sections = publish.book_sections(book)
    assert [(s.path.relative_to(book).as_posix(), s.kind) for s in sections] == [
        ("campaign.md", "overview"),
        ("chapters/01-the-drowned-coast/chapter.md", "chapter"),
        ("chapters/01-the-drowned-coast/adventures/01-smugglers-cove.md", "adventure"),
        ("chapters/01-the-drowned-coast/encounters/01-harbor-brawl.md", "encounter"),
        ("npcs.md", "index"),
        ("items.md", "index"),
        ("locations.md", "index"),
    ]


def test_readiness_reports_placeholders_empty_sections_and_details(book: Path) -> None:
    write(book / "chapters/01-the-drowned-coast/adventures/02-the-wreck.md",
          "# The Wreck\n\n## Scenes\n\n_To be written._\n\n## Aftermath\n")
    issues = [(i.file, i.message) for i in publish.readiness(book)]
    wreck = "chapters/01-the-drowned-coast/adventures/02-the-wreck.md"
    assert (wreck, "Placeholder text: not written yet.") in issues
    assert (wreck, "The 'Aftermath' section is empty.") in issues
    assert (wreck, "The adventure has no map. Fine if none is needed.") in issues
    assert (".campaign/publish.json", "No author name for the title page.") in issues
    assert (".campaign/publish.json", "No edition recorded, such as '1.0'.") in issues


def test_publish_details_are_saved_and_reused(book: Path) -> None:
    result = publish.set_publish_details(
        book, edition="1.0", author="A. Author", copyright_holder="A. Author",
        page_size="a4",
    )
    assert result["edition"] == "1.0"
    assert result["details"]["page_size"] == "A4"
    saved = json.loads((book / ".campaign/publish.json").read_text())
    assert saved["author"] == "A. Author"
    assert json.loads((book / ".campaign/campaign.json").read_text())["edition"] == "1.0"
    publish.set_publish_details(book, credits="Maps by B.")
    details = publish.read_details(book)
    assert details["author"] == "A. Author" and details["credits"] == "Maps by B."
    with pytest.raises(ValueError, match="Letter or A4"):
        publish.set_publish_details(book, page_size="legal")
    with pytest.raises(ValueError, match="was not found"):
        publish.set_publish_details(book, cover_image="cover.png")


def test_publish_writes_a_navigable_pdf(book: Path) -> None:
    publish.set_publish_details(
        book, edition="1.0", author="A. Author", copyright_holder="A. Author",
        footer_notice=True, license_text="Includes SRD 5.2 material (CC-BY-4.0).",
    )
    before = {p: p.read_bytes() for p in book.rglob("*") if p.is_file()}
    result = publish.publish(book)
    after = {p: p.read_bytes() for p in book.rglob("*") if p.is_file() and "published" not in
             p.parts}
    assert after == before

    [made] = result["files"]
    assert made["pdf"].endswith("published/the-sunken-crown-1-0-letter.pdf")
    assert made["sections"] == 7 and made["maps"] == 2 and made["encounter_trackers"] == 1
    reader = pypdf.PdfReader(made["pdf"])
    assert reader.metadata["/Author"] == "A. Author"
    assert reader.metadata["/copyright"].startswith("© ")
    assert reader.metadata["/edition"] == "1.0"
    assert outline(reader) == [
        "Contents", "The Sunken Crown", "The Drowned Coast", "Smugglers' Cove",
        "Harbor Brawl", "Key NPCs", "Key items", "Key locations",
    ]
    content = text(reader)
    assert "Edition 1.0" in content and "Includes SRD 5.2 material" in content
    assert "Appendix: Key NPCs" in content
    assert "GETTING_STARTED" not in content and "Work log" not in content
    links = [
        annotation.get_object()
        for page in reader.pages
        for annotation in page.get("/Annots", [])
        if annotation.get_object().get("/Subtype") == "/Link"
    ]
    assert links, "cross-references should be clickable"
    assert "note" not in result  # published/ is in the campaign's .gitignore


def test_encounter_tracker_gets_its_own_page(book: Path) -> None:
    reader = pypdf.PdfReader(publish.publish(book)["files"][0]["pdf"])
    [tracker_page] = [p.extract_text() for p in reader.pages if "Encounter tracker" in
                      p.extract_text()]
    assert "Encounter summary" not in tracker_page


def test_maps_shown_once_and_linked_maps_go_to_an_appendix(book: Path) -> None:
    adventure = book / "chapters/01-the-drowned-coast/adventures/01-smugglers-cove.md"
    write(adventure, adventure.read_text() + "\n![World again](../../../maps/world.png)\n"
          "See the [harbor](../../../maps/harbor.png).\n")
    png(book / "maps" / "harbor.png")
    reader = pypdf.PdfReader(publish.publish(book)["files"][0]["pdf"])
    content = text(reader)
    assert "Map: World again (page" in content
    assert "Maps" in outline(reader)


def test_working_documents_and_outside_links_are_not_links(book: Path) -> None:
    write(book / "campaign.md", (book / "campaign.md").read_text()
          + "\nSee [open items](OPEN_ITEMS.md) and ![secret](../../../etc/passwd.png).\n")
    html, _ = publish.render_book(book, publish.read_details(book), None)
    assert 'href="OPEN_ITEMS.md"' not in html
    assert "[Missing image: secret]" in html


def test_running_copies_are_not_published(book: Path, tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(book)], check=True)
    subprocess.run(["git", "-C", str(book), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(book), "commit", "-qm", "init"], check=True)
    copy = Path(start_campaign(book, "Tuesday")["folder"])
    with pytest.raises(ValueError, match="running copy"):
        publish.publish(copy)
    assert publish.readiness(copy)[0].severity == "error"
    with pytest.raises(ValueError, match="master campaign"):
        publish.set_publish_details(copy, author="X")


def test_epic_publishes_one_pdf_per_book_in_reading_order(tmp_path: Path) -> None:
    saga = tmp_path / "saga"
    create_epic(saga, "The Tide Saga")
    create_campaign(saga / "deep-court", "The Deep Court")
    create_campaign(saga / "crown", "The Sunken Crown")
    write(saga / "epic.md", (saga / "epic.md").read_text()
          + "\n## Books\n\n1. [The Sunken Crown](crown/campaign.md)\n"
          "2. [The Deep Court](deep-court/campaign.md)\n")
    publish.set_publish_details(saga, edition="2.0", author="A. Author")
    result = publish.publish(saga, page_size="A4")
    names = [Path(f["pdf"]).name for f in result["files"]]
    assert names == ["01-the-sunken-crown-2-0-a4.pdf", "02-the-deep-court-2-0-a4.pdf"]
    first = text(pypdf.PdfReader(result["files"][0]["pdf"]))
    assert "Book 1 of The Tide Saga" in first and "A. Author" in first
    assert publish.read_details(saga / "crown")["author"] == "A. Author"


def test_publish_refuses_folders_that_are_not_campaigns(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a campaign"):
        publish.publish(tmp_path)


def test_readiness_asks_for_the_ogl_in_a_3_5_campaign(tmp_path: Path) -> None:
    keep = tmp_path / "keep"
    create_campaign(keep, "The Keep", rules="D&D 3.5")
    messages = [i.message for i in publish.readiness(keep)]
    assert any("Open Game License 1.0a" in m for m in messages)
    publish.set_publish_details(keep, license_text="OPEN GAME LICENSE Version 1.0a ...")
    assert not any("Open Game License 1.0a" in i.message for i in publish.readiness(keep))
