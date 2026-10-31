# Campaign Agent Design

How the Campaign Agent is built: its packaging, the files it reads and
writes, and the decisions behind them. For what the agent must do, see
[REQUIREMENTS.md](REQUIREMENTS.md); for how DMs use it, see the
[User Guide](USER_GUIDE.md).

## Packaging

The agent is a Claude Code plugin, installed once and used in any campaign
folder. Agent instructions live in the plugin, so improving the agent never
requires editing campaigns.

| Part | Where | Purpose |
|---|---|---|
| Agent rules | `plugin/skills/campaign-rules/` | Rules the agent follows in any campaign folder: one file per section, indexes kept consistent, stat block formats, encounter summaries and trackers. |
| Commands | `plugin/skills/<command>/` | One skill per command (see the User Guide's command list). |
| Campaign MCP server | `src/ai_campaign/`, started by `plugin/.mcp.json` | Python tools for work that needs real logic. |
| Scribe MCP server | `agents/scribe/`, its own plugin | Read-only queries of the Scribe's record for the DM and the agent. |

The plugin's `userConfig` option `python` names the interpreter that runs
the MCP server. The repository root is a local plugin marketplace named
`ai-pc`, so Claude Code reads the plugin straight from the clone.

### MCP tools

| Tool | Does |
|---|---|
| `campaign_status` | What a folder is (master, running copy, collection, epic, or none), its contents, the container it belongs to, and its git repository. |
| `check_campaign` | Structure checks for one campaign. Changes nothing. |
| `check_epic` | Checks across an epic's books, plus each book's checks. Changes nothing. |
| `create_campaign`, `create_collection`, `create_epic` | Set up a folder; commit it when in git; optionally `git init` first. |
| `ensure_campaign_docs` | Adds missing working documents without touching existing files. |
| `snapshot_campaign` | Commits the folder, or writes a zip snapshot. |
| `start_campaign` | Makes a running copy. |
| `encounter_xp` | Encounter arithmetic for the campaign's rules edition. |
| `publish_readiness`, `set_publish_details`, `publish_campaign` | Release 2 publishing. |
| `extract_pdf_text` | Selectable text from PDF starting material, up to 500 KB. |

Tools refuse with a `ToolError` whose message explains what to do, because
the MCP SDK hides other exception messages from Claude.

### Modules

| Module | Contents |
|---|---|
| `mcp_server.py` | The MCP tools |
| `structure.py` | Reading and checking campaign folders: chapters, links, indexes, maps |
| `lifecycle.py` | Creating campaigns, collections, and epics; running copies; snapshots; the generated working documents |
| `gitops.py` | Git commands, with commits scoped to one folder |
| `containers.py` | Collection and epic markers and membership |
| `epic.py` | Book order and checks across an epic's books |
| `encounters.py` | 5e XP and difficulty; 3.5 Encounter Level, difficulty, and XP |
| `systems.py` | Supported rules editions and their SRD attribution |
| `publish.py` | Publishing readiness, publishing details, and the PDF |
| `marker.py` | The campaign marker |
| `pdf.py` | PDF text extraction |

## Campaign folder

```text
<campaign>/
  campaign.md
  GETTING_STARTED.md        # working documents
  OPEN_ITEMS.md
  WORKLOG.md
  npcs.md                   # indexes
  items.md
  locations.md
  maps/
    <map>.png
  chapters/
    01-<chapter>/
      chapter.md
      adventures/
        01-<adventure>.md
      encounters/
        01-<encounter>.md
  sessions/                 # running copy only, written by the Scribe
    2026-10-20.md
  .scribe/                  # running copy only, the Scribe's data
  .campaign/
    campaign.json           # the campaign marker
    publish.json            # publishing details, once set
    snapshots/              # zip snapshots, only without git
  published/                # PDFs from /publish-campaign
  .gitignore
```

- Empty `maps/`, `chapters/`, and `sessions/` folders hold a `.gitkeep` so
  git keeps them.
- Number prefixes (`01-`) order chapters, adventures, and encounters; the
  checks warn about missing or repeated numbers.
- Maps are linked with relative image embeds, such as
  `![Smugglers' cove](../../../maps/cove.png)`, so they show in the
  Markdown preview.
- Index entries are `## <name>` headings with `- **Field:** value` lines.
  The epic checks read the `Status` and `Fate` fields.
- Encounter files have `## Encounter summary` and `## Encounter tracker`
  sections, which the checks look for and Publish puts on its own page.
- `GETTING_STARTED.md` and `WORKLOG.md` links are not checked: the guide is
  generated and the work log is history.
- The new-campaign `.gitignore` excludes `.env`, `.scribe/`,
  `.campaign/snapshots/`, and `published/`.

### Campaign marker

`.campaign/campaign.json` records what kind of campaign folder this is. Only
the tools write it.

| Key | Meaning |
|---|---|
| `role` | `master` or `running`. |
| `title` | The campaign's title. |
| `created` | Date the master was created. |
| `format_version` | Version of the marker format, currently 1. |
| `rules` | The rules edition, such as `D&D 5e (2024)`. |
| `edition` | The master's published edition. |
| `source_master` | Running copy only: the master folder it was made from. |
| `source_commit` | Running copy only: the master's git commit it was made from. |
| `group` | Running copy only: the group it is for. |
| `started` | Running copy only: date it was started. |

Keys the tools don't recognize are kept when the marker is rewritten, so
later versions and the Scribe can add their own, such as the group's
Discord channel and whether a session is open.

### Collection and epic markers

A collection is marked by `.campaign/collection.json` (`title`, `created`),
an epic by `.campaign/epic.json` (`title`, `created`, `rules`, and
`edition` once published). Their campaigns are ordinary subfolders with
their own campaign markers; `containers.members` lists the direct
subfolders that have one.

```text
<epic>/
  epic.md            story, rules edition, and ## Books: a numbered list linking each book's campaign.md
  npcs.md            epic-wide indexes, with Books and Fate fields
  items.md
  locations.md
  GETTING_STARTED.md
  OPEN_ITEMS.md
  WORKLOG.md
  .campaign/epic.json
  01-<book>/         a master campaign
```

Book order comes from the numbered items under `## Books` in `epic.md`;
books on disk but not listed follow, by folder name.

## Git

Every structure lives in one repository that the DM creates.

- **Folder-scoped commits.** `gitops.commit_folder` stages and commits only
  the given folder (`git add -A -- <folder>`, then `git commit -- <folder>`),
  so saving one campaign never sweeps in another in the same repository.
- **Snapshots** commit with the message `Snapshot: <summary>`; creation
  commits `Create campaign: <title>`. Without git, a snapshot is a zip in
  `.campaign/snapshots/`.
- **Running copies.** A master at the root of its repository is cloned
  (`git clone`). A master in a subfolder is copied to a sibling folder and
  committed in the same repository. Without git, it is a plain copy. The
  default name is `<master>--<group>`.
- The uncommitted-changes check before starting a copy looks only at the
  master's folder.

**Beta defaults**, to revisit after beta testing:

| Choice | Default | Alternatives considered |
|---|---|---|
| Where a running copy goes in a collection or epic | A sibling folder in the same repository | A separate repository; ask each time |
| Where publishing details live | `.campaign/publish.json`; the edition in the marker | Front matter in `campaign.md` |
| Where PDFs go | `published/` inside the campaign or epic | A folder outside the repository |

**History.** An earlier design gave each campaign its own repository and
joined collections and epics with git submodules. Beta testers liked the
structures but not submodules, so everything now lives in one repository.

## Encounters

`encounters.py` does the arithmetic so the agent never computes XP itself.
The rules edition picks the method (`systems.rules_family`):

| Edition | Method |
|---|---|
| D&D 5e (2024) | XP by CR; difficulty against the sum of each character's Low, Moderate, and High budgets. |
| D&D 5e (2014) | XP by CR only. |
| D&D 3.5 | Encounter Level from the creatures' combined power (each CR is worth 2^(CR/2); two of a CR make CR + 2); party level is the average, +1 for 6 or more characters, −1 for 3 or fewer; difficulty compares the two. XP per character approximates the DMG table: 300 × level, doubled per 2 CR above and halved per 2 below, 0 more than 7 below, and off the table more than 7 above. |

The tables were written from memory and must be checked against the
published rules before Release 2 is published.

## Publishing

`publish.py` builds a single HTML document from the campaign and renders it
with WeasyPrint, which needs the Pango system library.

- **Book order** comes from `book_sections`: `campaign.md`, then each
  chapter's `chapter.md`, adventures, and encounters, then the indexes.
- **Markdown** is converted with Python-Markdown. A tree processor gives
  every element an id unique in the book (`s-<section path>--<anchor>`),
  rewrites links to other sections into links inside the PDF, prints each
  map once and turns later uses into page references, unlinks working
  documents and anything outside the campaign, and wraps each encounter
  tracker for its own page.
- **Navigation:** headings that title a section get bookmark levels; the
  contents and map references use CSS `target-counter` for page numbers.
- **Metadata:** title, author, copyright, rights, edition, and rules go in
  the PDF's document properties.
- **Safety:** a URL fetcher loads only `file:` and `data:` URLs inside the
  campaign or epic, so nothing is fetched from the network.
- **Epics** render each book separately, with "Book N of <epic>" on the
  title page. Details are read from the epic's `publish.json` and then the
  book's, so a book can override the epic.
- **Output names:** `<title>-<edition>-<page size>.pdf`, prefixed with the
  book number in an epic.
