"""MCP server that gives Claude Code the Campaign Agent's campaign tools."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from ai_campaign import lifecycle, structure
from ai_campaign.pdf import extract_pdf_text as _extract_pdf_text

server = MCPServer(
    name="campaign",
    instructions=(
        "Tools for D&D campaign folders managed by the Campaign Agent. A master campaign "
        "is authored in Create Mode and never used to run games; a running copy is made "
        "from it for each group. Pass absolute folder paths; relative paths are resolved "
        "against the server's working directory."
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
    """Report whether a folder is a master campaign, a running copy, or not a campaign,
    and summarize its chapters, adventures, encounters, maps, indexes, and sessions."""
    with _reported():
        return structure.campaign_summary(_path(folder))


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
def create_campaign(folder: str, title: str, init_git: bool = False) -> dict[str, Any]:
    """Set up a new master campaign in an empty or new folder: campaign.md, the NPC, item,
    and location indexes, maps/ and chapters/ folders, the campaign marker, and a
    .gitignore. With init_git, the folder is made a git repository and committed."""
    with _reported():
        return lifecycle.create_campaign(_path(folder), title, init_git=init_git)


@server.tool()
def start_campaign(
    master_folder: str, group: str, destination: str | None = None
) -> dict[str, Any]:
    """Make a running copy of a master campaign for a group, with a sessions/ folder for the
    Scribe. Uses git clone when the master is a git repository (it must have no uncommitted
    changes) and a folder copy otherwise. By default the copy is created next to the master
    as '<master>--<group>'. Refuses to start from a running copy."""
    with _reported():
        return lifecycle.start_campaign(
            _path(master_folder), group, _path(destination) if destination else None
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
