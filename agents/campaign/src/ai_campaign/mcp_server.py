"""MCP server that gives Claude Code the Campaign Agent's campaign tools."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from ai_campaign import containers, encounters, epic, gitops, lifecycle, publish, structure
from ai_campaign.pdf import extract_pdf_text as _extract_pdf_text

server = MCPServer(
    name="campaign",
    instructions=(
        "Tools for D&D campaign folders managed by the Campaign Agent. A master campaign "
        "is authored in Create Mode and never used to run games; a running copy is made "
        "from it for each group. A collection holds independent campaigns in subfolders; an "
        "epic holds books (campaigns) in subfolders, tied together by epic.md. Pass absolute "
        "folder paths; relative paths are resolved against the server's working directory."
    ),
)


@contextmanager
def _reported() -> Iterator[None]:
    """Pass the reason for a refusal to Claude; MCP hides other exception messages."""
    try:
        yield
    except ValueError as error:
        raise ToolError(str(error)) from error


def _path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


@server.tool()
def campaign_status(folder: str) -> dict[str, Any]:
    """Report what a folder is: a master campaign, a running copy, a collection, an epic,
    or none of these. For a campaign, summarize its chapters, adventures, encounters, maps,
    indexes, and sessions, and say which collection or epic it belongs to. For a collection
    or epic, list its campaigns or books. Also report its git repository, if any."""
    with _reported():
        path = _path(folder)
        summary = structure.campaign_summary(path)
        container = containers.read_container(path)
        summary["container"] = container
        if container is not None:
            summary["members"] = containers.members(path)
            if container["kind"] == containers.EPIC:
                summary.update(epic.epic_summary(path))
        summary["belongs_to"] = containers.find_container(path)
        summary["git"] = gitops.info(path)
        return summary


@server.tool()
def check_campaign(folder: str) -> dict[str, Any]:
    """Check a campaign folder without changing anything. Reports broken links, unlinked
    maps, unsupported map formats, index entries that link to no section, sections missing
    from their chapter or campaign outline, numbering problems, and missing required files.
    Errors are listed before warnings."""
    with _reported():
        issues = structure.check_campaign(_path(folder))
    return {
        "errors": sum(issue.severity == "error" for issue in issues),
        "warnings": sum(issue.severity == "warning" for issue in issues),
        "issues": structure.issues_as_dicts(issues),
    }


@server.tool()
def create_campaign(
    folder: str, title: str, rules: str | None = None, init_git: bool = False
) -> dict[str, Any]:
    """Set up a new master campaign in an empty or new folder: campaign.md (with the rules
    edition and its SRD attribution), the NPC, item, and location indexes, maps/ and
    chapters/ folders, GETTING_STARTED.md, OPEN_ITEMS.md, WORKLOG.md, the campaign marker,
    and a .gitignore. In an epic's subfolder the campaign is a book and uses the epic's
    rules edition; otherwise the default is D&D 5e (2024). Pass rules only when the DM names
    an edition. If the folder is in a git repository, the new files are committed; if not
    and init_git is true, a repository is created in the folder first."""
    with _reported():
        return lifecycle.create_campaign(_path(folder), title, rules=rules, init_git=init_git)


@server.tool()
def create_collection(folder: str, title: str, init_git: bool = False) -> dict[str, Any]:
    """Make a folder a collection: independent campaigns, each in its own subfolder of the
    same git repository. Adds a README.md and the collection marker, and lists campaigns
    already in its subfolders. With init_git, creates a git repository in the folder first
    if it is not in one."""
    with _reported():
        return lifecycle.create_collection(_path(folder), title, init_git=init_git)


@server.tool()
def create_epic(
    folder: str, title: str, rules: str = lifecycle.DEFAULT_RULES, init_git: bool = False
) -> dict[str, Any]:
    """Make a folder an epic: one long story told as books, each book a campaign in its own
    subfolder. Adds epic.md (story, rules edition, and the Books list in reading order),
    epic-wide NPC, item, and location indexes, GETTING_STARTED.md, OPEN_ITEMS.md, WORKLOG.md,
    and the epic marker. Books created in its subfolders use its rules edition. With
    init_git, creates a git repository in the folder first if it is not in one."""
    with _reported():
        return lifecycle.create_epic(_path(folder), title, rules=rules, init_git=init_git)


@server.tool()
def check_epic(folder: str) -> dict[str, Any]:
    """Check an epic's books against each other without changing anything: books missing
    from or wrongly listed in epic.md, rules editions that differ, broken links, NPCs who
    die (or items destroyed, places lost) in one book but are key entries in a later book,
    entries that recur across books but are missing from the epic's indexes, and each
    book's own campaign checks. Story review is left to the agent."""
    with _reported():
        issues = epic.check_epic(_path(folder))
    return {
        "errors": sum(issue.severity == "error" for issue in issues),
        "warnings": sum(issue.severity == "warning" for issue in issues),
        "issues": structure.issues_as_dicts(issues),
    }


@server.tool()
def encounter_xp(
    creatures: list[dict[str, Any]],
    party_levels: list[int],
    rules: str = lifecycle.DEFAULT_RULES,
) -> dict[str, Any]:
    """Work out an encounter's XP and difficulty. creatures is a list of
    {"name": ..., "cr": "1/4", "count": 3}; party_levels lists each character's level,
    such as [3, 3, 3, 3]; rules is the campaign's rules edition. For D&D 5e, returns XP per
    creature and in total and XP per character, and for the 2024 rules the Low, Moderate,
    and High XP budgets and the difficulty. For D&D 3.5, returns the Encounter Level, the
    party level, the difficulty (Easy, Challenging, Very difficult, Overpowering), and an
    approximate XP award for each character. Use it for every encounter summary instead of
    doing the arithmetic yourself."""
    with _reported():
        return encounters.encounter_xp(creatures, party_levels, rules)


@server.tool()
def ensure_campaign_docs(folder: str) -> dict[str, Any]:
    """Add GETTING_STARTED.md, OPEN_ITEMS.md, and WORKLOG.md to a campaign that lacks them,
    such as one created by an earlier version. Existing files are never changed."""
    with _reported():
        return lifecycle.ensure_campaign_docs(_path(folder))


@server.tool()
def snapshot_campaign(folder: str, summary: str) -> dict[str, Any]:
    """Save the current state of a campaign, collection, or epic so the DM can return to
    it. In a git repository, commits the changes inside that folder only, with the message
    'Snapshot: <summary>'; otherwise writes a zip file to .campaign/snapshots/. Update
    WORKLOG.md and OPEN_ITEMS.md before calling this so the snapshot includes them."""
    with _reported():
        return lifecycle.snapshot_campaign(_path(folder), summary)


@server.tool()
def start_campaign(
    master_folder: str, group: str, destination: str | None = None
) -> dict[str, Any]:
    """Make a running copy of a master campaign for a group, with a sessions/ folder for the
    Scribe, created next to the master as '<master>--<group>' unless a destination is given.
    A master at the root of its git repository is cloned; a master in a subfolder of a
    repository (such as in a collection or epic) is copied to a sibling folder and committed
    in the same repository. The master must have no uncommitted changes. Refuses to start
    from a running copy."""
    with _reported():
        return lifecycle.start_campaign(
            _path(master_folder), group, _path(destination) if destination else None
        )


@server.tool()
def publish_readiness(folder: str) -> dict[str, Any]:
    """Check whether a master campaign, or every book of an epic, is ready to publish,
    without changing anything: the campaign (or epic) checks, plus placeholder text, empty
    sections, adventures with no map, and missing publishing details such as the author,
    copyright holder, and edition. The author decides what to fix before publishing."""
    with _reported():
        issues = publish.readiness(_path(folder))
    return {
        "errors": sum(issue.severity == "error" for issue in issues),
        "warnings": sum(issue.severity == "warning" for issue in issues),
        "issues": structure.issues_as_dicts(issues),
    }


@server.tool()
def set_publish_details(
    folder: str,
    edition: str | None = None,
    author: str | None = None,
    copyright_holder: str | None = None,
    copyright_year: int | None = None,
    rights: str | None = None,
    license_text: str | None = None,
    credits: str | None = None,
    cover_image: str | None = None,
    footer_notice: bool | None = None,
    page_size: str | None = None,
    map_appendix: bool | None = None,
) -> dict[str, Any]:
    """Save publishing details for a master campaign or an epic, reused by every edition.
    Only the values given are changed. edition (such as "1.0") goes in the campaign or epic
    marker; the rest in .campaign/publish.json. rights defaults to "All rights reserved.";
    license_text holds license or attribution text, such as the SRD's CC-BY-4.0 notice;
    credits is Markdown; cover_image is a path relative to the folder; footer_notice puts
    the copyright line at the foot of every page; page_size is Letter or A4; map_appendix
    adds full-page copies of every map. Books of an epic use the epic's details unless
    they set their own."""
    with _reported():
        return publish.set_publish_details(
            _path(folder),
            edition=edition,
            author=author,
            copyright_holder=copyright_holder,
            copyright_year=copyright_year,
            rights=rights,
            license_text=license_text,
            credits=credits,
            cover_image=cover_image,
            footer_notice=footer_notice,
            page_size=page_size,
            map_appendix=map_appendix,
        )


@server.tool()
def publish_campaign(
    folder: str,
    page_size: str | None = None,
    map_appendix: bool | None = None,
    output_folder: str | None = None,
) -> dict[str, Any]:
    """Publish a master campaign as a digital PDF: title page, copyright page, contents,
    the overview, chapters with their adventures and encounters, each encounter tracker on
    its own page, and the indexes as appendices, with bookmarks and clickable links. An
    epic is published as one PDF per book, in reading order. Writes only to the output
    folder (default: published/ inside the folder); campaign files are never changed.
    Refuses running copies. page_size and map_appendix override the saved details for this
    publish only. Run publish_readiness first."""
    with _reported():
        return publish.publish(
            _path(folder),
            page_size=page_size,
            output_folder=_path(output_folder) if output_folder else None,
            map_appendix=map_appendix,
        )


@server.tool()
def extract_pdf_text(pdf_path: str) -> dict[str, Any]:
    """Extract the selectable text from a PDF of starting material. Scanned PDFs without an
    OCR text layer and password-protected PDFs are not supported."""
    with _reported():
        text = _extract_pdf_text(_path(pdf_path))
    return {"characters": len(text), "text": text}


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
