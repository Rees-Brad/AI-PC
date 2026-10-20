"""MCP server for private DM queries of the Scribe's record.

Answers go only to the DM (in Claude Code), never to Discord, so these tools can
include DM-private notes. The database is opened read-only; the Scribe's writes
happen elsewhere.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy.orm import Session

from ai_pc_shared.campaign.db import make_campaign_session_factory, open_campaign_readonly
from ai_scribe.config import database_path, load_settings
from ai_scribe.llm import queries

server = MCPServer(
    name="scribe",
    instructions=(
        "Read-only access to the Scribe's record of what happened at the table: session "
        "recaps, plot threads, NPCs, locations, and factions, who knows what, and the DM's "
        "private notes. Answers are for the DM only. For a Campaign Agent running copy, "
        "pass its absolute folder as campaign_folder; otherwise the Scribe's configured "
        "database is used."
    ),
)


@contextmanager
def _record(campaign_folder: str | None) -> Iterator[Session]:
    """A read-only session on the right database, with refusals passed to Claude."""
    try:
        folder = None
        if campaign_folder:
            folder = Path(campaign_folder).expanduser()
            if not folder.is_absolute():
                folder = Path.cwd() / folder
        path = database_path(load_settings(folder))
        if not path.is_file():
            raise ValueError(
                "The Scribe has not recorded anything for this campaign yet "
                f"(no database at {path})."
            )
        factory = make_campaign_session_factory(open_campaign_readonly(path))
        with factory() as session:
            yield session
    except ValueError as error:
        raise ToolError(str(error)) from error


def _ask(campaign_folder: str | None, query: Callable[[Session], str]) -> str:
    with _record(campaign_folder) as session:
        return query(session)


@server.tool()
def list_sessions(campaign_folder: str | None = None) -> str:
    """List recorded sessions with their dates, whether each is final, and the summary file
    written for it."""
    return _ask(campaign_folder, queries.sessions)


@server.tool()
def recap(session_id: str | None = None, campaign_folder: str | None = None) -> str:
    """The recap of a session, or of the most recent session when no session_id is given.
    A session in progress has a recap of the play so far."""
    if session_id:
        return _ask(campaign_folder, lambda s: queries.session_recap(s, session_id))
    return _ask(campaign_folder, queries.recap)


@server.tool()
def lookup(name: str, campaign_folder: str | None = None) -> str:
    """What the party knows about an NPC, location, or faction, and when it last came up."""
    return _ask(campaign_folder, lambda s: queries.lookup(s, name))


@server.tool()
def open_threads(campaign_folder: str | None = None) -> str:
    """Plot threads that are still open: unresolved hooks, accepted quests, and promises."""
    return _ask(campaign_folder, queries.threads)


@server.tool()
def who_knows(event: str, campaign_folder: str | None = None) -> str:
    """Which characters are aware of an event, and whether each knows it firsthand or
    secondhand. Awareness is inferred from play and can be wrong."""
    return _ask(campaign_folder, lambda s: queries.knows(s, event))


@server.tool()
def dm_notes(campaign_folder: str | None = None) -> str:
    """The DM's private notes. Never share these with players."""
    return _ask(campaign_folder, queries.dm_notes)


@server.tool()
def search_record(text: str, campaign_folder: str | None = None) -> str:
    """Find every recap, thread, NPC, location, faction, awareness record, and DM note that
    mentions the text. Use it for questions the other tools do not answer directly."""
    return _ask(campaign_folder, lambda s: queries.search(s, text))


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
