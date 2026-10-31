# Campaign Agent User Guide

This guide is for DMs and campaign authors. It explains how to work with the
Campaign Agent: setting up your workspace, choosing how to organize your
campaigns, creating and checking them, running them with a group, and
publishing them. To install the agent, see the [README](README.md).

The guide covers what the agent does today. Game Session and Update modes,
which work with the Scribe during and after play, are still being built; see
[REQUIREMENTS.md](REQUIREMENTS.md) for what is planned.

## What the Campaign Agent is

The Campaign Agent helps you write your campaign. It does not write the
campaign for you. You bring the story and make the decisions; the agent asks
questions, offers options, and takes on the rote work: names for minor NPCs
and places, stat blocks, encounter arithmetic, keeping indexes and links
current, and checking the campaign for story holes. It does as much or as
little as you want.

The agent is for the DM only. Campaign files hold plans your players must
not see, so players never use it. During play, they ask the Scribe about
what has happened.

## Your workspace

The agent runs in VS Code, with Claude Code as the conversation. Open your
campaign folder as the VS Code workspace and arrange it like this:

```text
┌────────────┬──────────────────────┬──────────────────┬──────────────┐
│ Explorer   │ Adventure (Markdown  │ Map (image)      │ Claude Code  │
│ (campaign  │ preview)             │                  │ (agent chat) │
│ tree)      │                      │                  │              │
└────────────┴──────────────────────┴──────────────────┴──────────────┘
```

- **Explorer:** the whole campaign: chapters, adventures, encounters, maps,
  and session summaries.
- **Markdown preview:** press Ctrl+Shift+V (Cmd+Shift+V on a Mac) to read a
  section formatted. Drag the tab to a split to keep it beside the map.
- **Map:** open the map for the section you are working on, so you can see
  it while you write.
- **Claude Code:** talk to the agent in plain language. Commands start the
  main tasks, but you don't need one for every request.

Every change the agent makes to a file is shown to you first, and nothing
is written until you accept it. Actions such as creating a campaign ask for
your approval before they run.

You use your own Claude account. No keys or passwords are stored in your
campaign folders.

## Choosing how to organize your campaigns

Each campaign lives in a git repository you create. Git keeps a history of
every change, so you can see what changed and roll back. Campaigns work
without git, but then snapshots are zip files and you lose the history. If
you forget to create the repository, the agent offers to.

One repository holds one of three structures:

| Structure | Choose it when | Set it up |
|---|---|---|
| **Single campaign** | You are writing one campaign. | Create the repository, open it in VS Code, and run `/create-campaign`. |
| **Collection** | You keep several independent campaigns together, such as one-shots or a set per level range. | Run `/create-collection` in the repository's folder, then make a subfolder for each campaign and run `/create-campaign` in it. |
| **Epic** | You are telling one long story as a series of books, where characters, places, and threads carry from book to book. | Run `/create-epic` in the repository's folder, then make a subfolder for each book and run `/create-campaign` in it. See [Epics](#epics). |

For example, to start a single campaign:

```bash
mkdir sunken-crown && cd sunken-crown && git init
code .
```

Then run `/create-campaign` in Claude Code.

You can't create a campaign inside another campaign, or an epic inside a
collection or another epic.

## Creating a campaign

Run `/create-campaign` in an empty folder. The agent asks for a title and
sets up the campaign, then develops it with you. Start by describing your
story or premise and what you want the players to experience.

The agent creates:

```text
campaign.md           overview, goal, rules edition, story, links to chapters and indexes
npcs.md               key NPCs
items.md              key items
locations.md          key locations
maps/                 your map images
chapters/
  01-<chapter>/
    chapter.md        the chapter's place in the story
    adventures/
      01-<adventure>.md
    encounters/
      01-<encounter>.md
GETTING_STARTED.md    a short version of this guide, inside your campaign
OPEN_ITEMS.md         your to-do list
WORKLOG.md            a journal of each working session
```

- A campaign needs at least a goal and one adventure with one encounter.
- The campaign is organized like a book: chapters move the story along,
  and each chapter holds adventures and standalone encounters. Number
  prefixes keep them in story order.
- Each section is its own file, so you can open, move, and link sections
  individually.
- An adventure you will run at the table is self-contained: it has
  everything you need for that session, so you never have to open another
  file mid-game.
- The structure can change as you go. Ask the agent to add, drop, or move
  chapters and adventures. It updates links and indexes, then checks the
  story for problems the move caused, such as a clue that now comes after
  the scene that needs it.
- You can give the agent starting notes: a text file, or a PDF with
  selectable text. Scanned PDFs need OCR first. Very large PDFs, such as a
  full rulebook, are too big.

### Game systems

The rules edition is recorded in `campaign.md`. Name an edition when you
create the campaign; otherwise the agent uses D&D 5e (2024).

| System | What the agent does |
|---|---|
| **D&D 5e (2024)**, the default | Stat blocks from the SRD 5.2 or written new. Encounters are rated Low, Moderate, or High. |
| **D&D 5e (2014)** | Stat blocks from the SRD 5.1 or written new. The agent works out XP; it rates difficulty itself and says so. |
| **D&D 3.5** | 3.5 stat blocks from the SRD 3.5 or written new. Encounters get an Encounter Level and are rated Easy, Challenging, Very difficult, or Overpowering. XP awards are approximate; check them against the Dungeon Master's Guide. |
| **Other systems** | Not supported. You can still organize, check, and publish the campaign, but encounter tools and license text don't cover the system. |

The agent takes standard creatures only from the open-licensed System
Reference Document (SRD) for your edition, and keeps the SRD's
attribution in `campaign.md`. It never copies stat blocks from other books,
so your campaign stays yours to share or sell.

## Encounters

Every encounter can be run from its file alone.

- **Encounter summary** at the top: the party it is built for, each
  creature's Challenge Rating and count, and the fight's XP and difficulty.
  The numbers come from the agent's encounter calculator, not guesswork.
- **Stat blocks** for every creature, in your edition's format. A named NPC
  who fights gets their own stat block, built from a base creature.
- **Encounter tracker** at the end: a table with one row per creature for
  AC, HP, damage taken, conditions, and initiative, to print and write on.

Ask for difficulty variants, such as a harder version in case the first
fight is too easy; each gets its own summary line and tracker rows.

## Indexes

Every campaign keeps three indexes so you can find what matters quickly,
while preparing and at the table:

| Index | File | Holds |
|---|---|---|
| Key NPCs | `npcs.md` | Allies, villains, quest givers, and anyone the party must meet again |
| Key items | `items.md` | Magic items and artifacts that matter to the story |
| Key locations | `locations.md` | Cities, dungeons, strongholds, and important sites |

Each entry has a short description, its role in the story, and links to the
sections where it appears. Minor NPCs and ordinary items stay in their
adventures. The indexes include your secrets; they are your view of the
campaign, not what the players know.

## Maps

Maps are images you make in another tool, such as Inkarnate or Dungeondraft.

- Save maps as PNG, JPEG, or WebP into `maps/`, for example by dragging
  them into the Explorer. Export TIFF, SVG, or PDF maps as images first.
- Ask the agent to add a map to a section. It proposes an image link, so
  the map shows in the section's preview.
- One map can serve several sections, such as a city map used by a chapter
  and two of its adventures.
- To update a map, save the new version under the same name. Every link
  keeps working.
- Ask the agent about a map and it reads it with the section's text. It
  tells you when a label is unreadable rather than guessing.
- Keep your map tool's project files outside `maps/`.

Where maps usually go:

| Section | Maps | Examples |
|---|---|---|
| Campaign | One or more | World map, continent map |
| Chapter | Any | Region map, city map |
| Adventure | Any | Dungeon, encounter area |

## Working across days

Building a campaign takes many sittings. Three working documents keep your
progress so you never need to scroll back through the chat:

| File | What it is |
|---|---|
| `GETTING_STARTED.md` | A short guide to working on this campaign. |
| `OPEN_ITEMS.md` | Open questions and unfinished work, linked to the files concerned. The agent checks items off as they are done. Reorder items or mark them **(priority)** to steer what it works on next. |
| `WORKLOG.md` | A journal, newest first: what was done and decided in each session, and ideas set aside. |

- **Before you stop**, run `/save-campaign`. The agent updates the work log
  and open items, checks the campaign, and takes a snapshot: a git commit,
  or a zip file in `.campaign/snapshots/` without git. In a collection or
  epic, only the folder you save from is committed.
- **To resume**, open the folder and run `/create-campaign`. The agent reads
  the work log and open items and suggests what to do next.
- Claude Code also keeps your conversations. Reopen one from the past
  conversations button in the Claude Code panel, or with `/resume`.

Campaigns made with an earlier version get the working documents added the
next time you run `/create-campaign` in them.

## Checking your campaign

`/check-campaign` reports problems without changing anything:

- broken links, and links that point outside the campaign;
- maps that no section links to, and unsupported map formats;
- index entries that link to no section;
- chapters, adventures, or encounters missing from their outlines;
- numbering problems, such as two chapters numbered `02`;
- encounters missing their summary or tracker;
- a missing goal, rules edition, or adventure.

A new campaign reports that it has no goal and no adventure yet; that is
expected. The agent offers to fix what it finds.

## Epics

An epic is one long story told as books, like a fantasy series. Each book
is a full campaign in its own subfolder.

```text
<epic>/
  epic.md        the epic's story, rules edition, and Books list in reading order
  npcs.md        NPCs who matter across books
  items.md       items that matter across books
  locations.md   places that matter across books
  01-<book>/     a book: a full campaign
  02-<book>/
```

- `epic.md` lists the books in reading order. The agent keeps the list
  current as you add, rename, or reorder books.
- Every book uses the epic's rules edition.
- When an NPC, item, or place matters in more than one book, give it an
  entry in the epic's index, with **Books** (where it appears) and **Fate**
  (what becomes of it, such as "Book 3: dies").
- In a book's own indexes, record planned endings in **Status**, such as
  "dies at Gallows Cross".

`/check-epic` checks the books against each other, without changing
anything:

- books missing from the Books list, or listed wrongly or twice;
- a book using a different rules edition;
- an NPC who dies, an item destroyed, or a place lost in one book but still
  a key entry in a later book;
- entries that recur across books but are missing from the epic's index;
- each book's own checks.

Then the agent reviews the story across books: timelines, characters whose
motives change without reason, foreshadowing that never pays off, dropped
threads, and gaps in level ranges. It says how confident it is; you decide.

## Running a campaign with a group

The campaign you write is the **master**. Don't run games from it, because
play and the updates after each session change the files. Instead, run
`/start-campaign` in the master to make a **running copy** for one group,
and open that folder to run the group's games. One master can start any
number of groups.

- A single campaign's running copy goes next to the master, as
  `<master>--<group>`.
- In a collection or epic, the running copy is a sibling folder in the same
  repository.
- Save the master first: `/start-campaign` refuses when the master has
  unsaved changes, because the copy is made from the last save. It also
  refuses to start from a running copy, or into a folder that already
  exists.

The Scribe keeps its record of each session inside the running copy, and
writes a short summary of each session to `sessions/`. You can ask the
Scribe about past sessions privately in Claude Code at any time, for
example "what did the party promise the harbormaster?"

## Publishing a PDF (beta)

`/publish-campaign` turns a finished master campaign into a PDF for readers
or buyers.

1. **Readiness check.** The agent reports anything worth fixing: the usual
   checks, plus placeholder text, empty sections, adventures with no map,
   and missing publishing details. You decide whether to fix them or
   publish anyway.
2. **Publishing details.** The first time, the agent asks for the author,
   copyright holder, and edition, and offers options: a rights statement,
   license or attribution text, credits, a cover image, a copyright line in
   every page's footer, page size (Letter or A4), and a map appendix. They
   are saved and reused for every later edition.
3. **The PDF.** It is written to `published/` and the agent gives you a link.
   Review it before treating it as final.

The PDF has a title page, a copyright page, and contents, then the
overview, each chapter with its adventures and encounters, and the indexes
as appendices. Bookmarks and links between sections are clickable. Each map
is printed once, and later uses point to its page. Each encounter tracker
gets its own page. Your working documents are left out.

- **Epics** are published as one PDF per book, numbered in reading order.
  Details you set on the epic apply to every book.
- **Running copies** are never published, because they hold play history.
- Publishing never changes your campaign files. To fix something, change
  the campaign and publish again. With git, tag each edition, such as
  `edition-1.0`.
- **Rights are yours to check.** You must have the rights to everything you
  publish, including maps and artwork. SRD material needs its attribution.
  D&D 3.5 material needs the full Open Game License 1.0a text and its
  Section 15 notice in your license text; the readiness check reminds you.

Not yet available: the print-ready PDF for print-on-demand services,
watermarks, importing a published PDF, and styling themes.

## Commands

| Command | What it does |
|---|---|
| `/create-campaign` | Starts a new campaign in an empty folder, or resumes one. |
| `/check-campaign` | Checks the campaign without changing anything. |
| `/save-campaign` | Updates the work log and open items, checks, and takes a snapshot. |
| `/create-collection` | Makes a folder a collection of independent campaigns. |
| `/create-epic` | Starts or resumes an epic. |
| `/check-epic` | Checks an epic's books against each other and reviews the story. |
| `/start-campaign` | Makes a running copy of a master for a group. |
| `/publish-campaign` | Publishes a master as a PDF, or an epic as one PDF per book (beta). |

Claude Code may show commands with the plugin name first, such as
`/campaign-agent:create-campaign`.

For installation problems, see Troubleshooting in the [README](README.md).
