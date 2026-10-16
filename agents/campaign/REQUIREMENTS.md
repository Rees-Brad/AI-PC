# Campaign Agent Requirements

## Purpose

The Campaign Agent helps the DM create and maintain a long-running campaign.
It assists in developing the campaign's central story arc and a collection
of adventure modules, then helps adapt the remaining campaign after each
game session based on what actually happened at the table.

The campaign should have direction without forcing the players down a
single path. Side quests, alternate leads, and meaningful consequences
give the players room to choose what matters to them.

A campaign at a minimum must have:
  1. A goal (objective)
  2. One adventure with at least one encounter

The Campaign Agent works with the other agents to continually update
future modules to keep the story progressing. The first release pairs it
with the Scribe; the DM Agent is on hold, so the DM Agent's step below
describes the intended direction rather than first-release work.
A useful workflow could be:

1. Campaign Agent builds the central arc, setting, factions, key NPCs, and a collection of adventure modules. Each module can have multiple hooks, outcomes, and ways to connect back to the larger story.
2. Before game night, the Campaign Agent selects and adapts the next module based on where the characters are and what they’ve chosen to pursue.
3. DM Agent reviews it for playability and whether its events still fit the larger arc.
4. Scribe Agent checks campaign records for continuity: NPC relationships, unresolved events, character knowledge, and consequences that the draft might contradict.
5. Campaign Agent incorporates those reviews and offers side quests or alternate leads that feel connected to the world, while keeping the main arc available rather than compulsory.

The Campaign Agent is a tool for the DM. Players do not use it, because
campaign files contain plans the players must not see; during play, players
ask the Scribe about what has happened.

## Working Environment: VS Code and Claude Code

A campaign is a collection of files, not a single document, and the DM
needs to see that whole structure while working on any part of it. The
Campaign Agent therefore runs inside VS Code, with Claude Code as the
conversation with the agent. The browser-based interface from the first
version is retired.

```text
┌────────────┬──────────────────────┬──────────────────┬──────────────┐
│ Explorer   │ Adventure (Markdown  │ Map (image)      │ Claude Code  │
│ (campaign  │ preview)             │                  │ (agent chat) │
│ tree)      │                      │                  │              │
└────────────┴──────────────────────┴──────────────────┴──────────────┘
```

- The DM opens a campaign folder as the VS Code workspace. The Explorer
  shows the full campaign structure: campaign, chapters, adventures,
  encounters, maps, and session summaries.
- The DM can read any section as formatted Markdown (Markdown preview)
  while the map for that section is open beside it in a split editor.
  Seeing the map while an adventure is being developed is a core
  requirement, not an extra.
- The main interaction is an ongoing natural-language conversation in
  Claude Code. Commands start the main workflows (see Commands), but the
  DM does not need a command for every turn.
- Every file the agent creates or changes is shown to the DM as a change
  to review and accept before it is written. The agent never says a
  change was saved until the DM has accepted it.
- Each DM uses their own Claude account. No API keys or credentials are
  stored in the repository or in campaign folders.
- Everything runs on the DM's computer: VS Code, the Campaign Agent, the
  Scribe, and the campaign folders.

### Packaging

The Campaign Agent is installed once and then works in any campaign
folder. It is packaged as a Claude Code plugin made up of:

| Part | Purpose |
|---|---|
| Agent instructions | The Create and Update rules in this document, such as one file per section and keeping indexes consistent. |
| Commands | Entry points for the main workflows (see Commands). |
| Campaign MCP server | Python tools for work that needs real logic: checking campaign structure and links, finding broken references after a move, extracting text from PDF starting material, starting a running copy, and starting and stopping the Scribe for a game session. |
| Scribe MCP server | Read-only access to the Scribe's record so the DM and agent can ask the Scribe questions privately, outside Discord, at any time (see Collaboration with Other Agents). Provided by the Scribe agent. |

Campaign folders contain only campaign material. Agent instructions live in
the plugin, so improving the agent does not require editing every campaign.

### Commands

| Command | What it does |
|---|---|
| `/create-campaign` | Starts a new master campaign in the open folder, or resumes creation of an existing one. |
| `/start-campaign` | Makes a running copy of a master campaign for a group and sets up its `sessions/` folder. |
| `/start-session` | Enters Game Session Mode: starts the Scribe in the group's Discord channel and prepares the next adventure for quick reference. |
| `/end-session` | Ends Game Session Mode: tells the Scribe to finalize the session and leave the channel, then offers to begin Update Mode. |
| `/update-campaign` | Works through the latest session with the DM and the Scribe and proposes changes to the remaining campaign. |
| `/check-campaign` | Reports broken links, unlinked maps, index entries that point nowhere, and structure problems without changing anything. |

Command names are working names and can change during design.

## Campaign Lifecycle

```text
 Create ──► master campaign ──► Start ──► running copy ──► Game Session ──► Update ─┐
            (kept as authored)            (one per group)       ▲                    │
                                                                └────────────────────┘
```

1. **Create.** The DM and the Campaign Agent build the master campaign
   (Campaign Creation Mode).
2. **Start.** When the campaign is ready to run, the DM makes a running
   copy for a group. The master is saved as authored and is not used to run
   the game.
3. **Game Session.** At game night the DM starts a session. The Campaign
   Agent starts the Scribe in the group's Discord channel, and both are
   available for the rest of the session. The Scribe records what happens
   and saves a short summary when the session ends.
4. **Update.** After each session, the DM, the Campaign Agent, and the
   Scribe adjust the remaining campaign in the running copy.

A running copy alternates between Game Session Mode and Update Mode for the
rest of the campaign. The running copy records which state it is in, so a
session left open (for example after a crash) is noticed the next time the
DM opens the folder.

Update Mode changes campaign files to match what happened at the table.
Running a game directly from the master would overwrite the original
campaign, so:

- The agent explains the master/running-copy split when a campaign is
  first created and again when it is started.
- Each campaign folder records whether it is a master or a running copy,
  and a running copy records which master it came from. The marker's
  format is decided with the other metadata conventions.
- The agent refuses to run Game Session or Update Mode on a master campaign
  and offers to make a running copy instead.
- Create Mode works on a master. Structural fixes made to a running copy
  stay in that copy unless the DM brings them back to the master.
- One master can have several running copies, for example one per group.

### Git (recommended, optional)

Each campaign can be a git repository. Git is recommended because it turns
the master/running-copy split into history the DM can inspect, but every
workflow also works with plain folders.

- `/create-campaign` offers to initialize the master as a git repository.
  Creation checkpoints are commits, made when the DM asks.
- `/start-campaign` makes the running copy with `git clone` when the master
  is a git repository, and with a plain folder copy otherwise.
- After an update is accepted, the agent offers to commit it with a message
  that names the session, for example "Update after session 2026-10-20".
- VS Code's Source Control view shows exactly what each update changed, and
  any change can be rolled back.
- Fixes made to the master later, such as a corrected map, can be pulled
  into a running copy when the DM chooses. The agent never merges master
  changes on its own.
- Secrets and the Scribe's working data are excluded from commits by the
  campaign's `.gitignore`.
- Without git, the DM loses history and diffs but nothing else.

## Operating Modes

The Campaign Agent has three active modes:
  1. Campaign Creation Mode, which works on a master campaign
  2. Game Session Mode, which works on a running copy during play
  3. Update Mode, which works on a running copy between sessions

Reviewer Mode is deferred (see Deferred: Reviewer Mode).

### 1. Campaign Creation Mode

The DM provides an initial story or plot description, along with any
campaign goals and objectives. The DM and Campaign Agent then work
together to develop the idea into a master campaign.

- Creating a campaign can take many working sessions. The files on disk
  are the saved state, so the DM can stop at any point and resume later by
  opening the same folder. Sections can be created as placeholders and
  filled in later.
- The DM can optionally provide starting notes or a source document to
  inform campaign creation. Supported documents include text files and PDFs
  with selectable text; scanned PDFs without an OCR text layer are not
  supported.
- The agent asks questions and offers options to help flesh out the
  premise, central story arc, setting, themes, and intended player
  experience. The DM guides the direction and makes the final decisions.
- The agent supports player choice by developing optional paths, side
  quests, and meaningful alternatives to the main story route.
- The campaign is organized like a book: chapters progress the story,
  and each chapter contains one or more adventures or NPC encounters.
- Each campaign section is its own Markdown file, including the campaign
  overview, chapters, adventures, and standalone NPC encounters. When asked
  to set up a campaign scaffold, the agent creates `campaign.md`, a
  `chapter.md` for each chapter, and separate files for each adventure and
  standalone encounter. It never combines the campaign into one file.
- The structure is provisional and can change as development continues.
  The DM can add or drop chapters and adventures and move large portions,
  such as an adventure between chapters or several adventures into a new
  chapter.
- After a structural change, the agent reviews the story arc for breaks or
  issues the move introduced, such as a clue now appearing after the scene
  that needs it.
- When proposing a structural change, the agent updates the affected
  chapter and campaign indexes so they match the new structure. Dropped or
  moved sections must not leave stale or broken references.
- Structural changes are presented for the DM's review before they are
  applied, and existing material is never silently discarded.
- An adventure intended for a game session is self-contained: it includes
  the relevant background, scenes, NPCs, encounters, and running details
  the DM needs for that session. References to other campaign files may be
  included for broader context, but the DM does not need to open them to
  run the session.
- The agent builds and maintains the key NPC, item, and location indexes
  as the campaign develops (see Campaign Indexes).
- The agent keeps planned events distinct from events that have actually
  happened in play; the Scribe remains the source of truth for the latter.

### 2. Game Session Mode

The DM starts Game Session Mode at game night. The Campaign Agent starts the
Scribe and supports the DM during play; the Scribe records the session and
answers the table's questions about earlier sessions.

**Starting a session**

- `/start-session` works only on a running copy and only when no session
  is already open.
- The agent starts the Scribe for this running copy and tells it which
  Discord voice channel to join. The channel is saved with the running copy
  after the DM gives it the first time, and the DM can change it.
- The agent confirms to the DM that the Scribe has joined the channel, or
  reports clearly why it could not start it. A session can still be run
  without the Scribe if the DM chooses, but the agent warns that nothing
  will be recorded.
- The agent asks which adventure the party is likely to play, or suggests
  one from where the last session ended, and has it ready for reference.

**During the session**

- Players and the DM can ask the Scribe about earlier sessions through its
  Discord commands, such as who an NPC is or which threads are open. The
  whole table sees those answers.
- The DM can also ask the Scribe privately from VS Code, for example to
  check what the party knows before revealing a secret. Those answers go
  only to the DM and can include DM-private records.
- The DM can ask the Campaign Agent in VS Code for quick lookups: a stat
  block, an NPC's motives, what lies behind a door, where a magic item is
  hidden, or what an index says about a location. Answers draw on campaign
  material and the Scribe's record.
- The DM can ask for help improvising, such as a name for an unplanned NPC
  or a way to bring a wandering party back toward a hook. Suggestions stay
  in the conversation.
- The Campaign Agent speaks only to the DM. It never posts to Discord,
  because its answers can reveal plans the players must not see.
- The agent does not change campaign files during a session. What happens
  at the table is the Scribe's to record, and changes to the campaign wait
  for Update Mode. The DM can still edit files by hand.
- Answers must be fast and short enough to use at the table.

**Ending a session**

- `/end-session` tells the Scribe to finalize the session record, write its
  summary to `sessions/`, and leave the voice channel.
- The agent confirms the summary was written, then offers to start Update
  Mode now or later.
- If the Scribe stops unexpectedly during a session, the agent tells the DM
  and offers to restart it.

### 3. Update Mode

After each session, or at the latest before the next one, the DM, the
Campaign Agent, and the Scribe work together in the running copy to adjust
the rest of the campaign based on what happened at the table.

- Update Mode works only on a running copy (see Campaign Lifecycle).
- The agent starts from the Scribe's summary for the latest session in
  `sessions/` and asks the Scribe for details as needed: who was met, what
  was promised, which threads are open, which characters know what.
- The DM can ask the Scribe questions directly in the same conversation,
  such as "what did the party promise the harbormaster?"
- The agent reviews completed events, character decisions, NPC
  interactions, and changes to open story threads, then proposes how the
  remaining campaign should change. It raises these suggestions itself
  rather than waiting to be asked. Examples:
  - **The characters leveled up.** The agent proposes adjusting the
    remaining encounters to the party's new level.
  - **The encounters are not challenging the players.** The agent proposes
    raising the difficulty of upcoming encounters, and says which ones and
    how.
  - **The players killed a critical NPC** whom they were meant to meet
    again for important information. The agent proposes a new way for that
    information to reach the party, such as a new NPC who carries it, and a
    fallback, such as a book containing it, in case the players kill that
    NPC too.
- The agent calculates experience points earned from fights, checks
  whether characters qualify to level up under the campaign's advancement
  rules, and surfaces the results for the DM to confirm.
- Revisions preserve continuity while allowing the story to change in
  response to player choices. The main arc stays available rather than
  compulsory.
- The agent proposes updates to the campaign indexes to match the session,
  such as marking an NPC as dead, an artifact as now carried by the party,
  or a location as visited, and adds any new NPC, item, or location that
  became important.
- The agent changes campaign material only. It never edits files in
  `sessions/` or the Scribe's database; corrections to what happened go
  through the Scribe (see the Scribe's DM authority rules).
- The DM has final authority over XP awards, level advancement, encounter
  rulings, and campaign changes. Every suggestion is a proposal the DM can
  accept, change, or reject.

### Deferred: Reviewer Mode

Reviewer Mode, in which the agent reviews a supplied campaign document
without writing any files, is set aside while the VS Code design is built.
Its earlier requirements are kept here for when it returns:

- The agent analyzes only the supplied material and returns feedback:
  strengths, unclear points, inconsistencies, risks, and opportunities.
- Suggestions are advisory; the agent creates, edits, or rewrites no files.
- The agent does not assume details absent from the supplied material and
  identifies missing context where it affects its feedback.
- Supported documents are text files and PDFs with selectable text.

## Core Responsibilities

- Develop the campaign premise, setting, themes, major story arc, and
  important factions, locations, and NPCs.
- Create and maintain a collection of adventure modules that can advance,
  complicate, or otherwise connect to the larger campaign.
- Before a game night, adapt the selected adventure to the characters'
  current circumstances, prior choices, and established story position.
- Offer relevant side quests and alternate paths so the campaign does not
  depend on a single required route.
- Track unresolved campaign plans and distinguish intended future events
  from events that have actually happened in play.

## Collaboration with Other Agents

### DM Agent (on hold)

Not part of the first release. The DM reviews a prepared adventure for playability and fit with the
campaign's story arc. The Campaign Agent can revise the adventure in
response to that review. The DM remains the final authority over what
happens at the table.

### Scribe Agent

The Scribe records what happens at the table; campaign plans describe what
may happen. The Campaign Agent uses the Scribe's record to keep new
material consistent with play.

- The Campaign Agent starts the Scribe at the beginning of each game
  session, tells it the Discord channel, and tells it to finalize and leave
  when the session ends (see Game Session Mode).
- Once a campaign is started, the Scribe saves its data inside the running
  copy instead of in a separate location (see the Scribe's requirements).
- After each session the Scribe saves a short Markdown summary in
  `sessions/`, named by the session date. More detail comes from asking the
  Scribe.
- Players ask the Scribe questions in Discord. The DM and the Campaign
  Agent can also query the Scribe privately, outside Discord, through its
  read-only query tools at any time, including during a session. These
  offer the same lookups as its Discord commands (recaps, NPCs, locations,
  open threads, and who knows what) and can include DM-private records.
- The Scribe checks proposed material against the record, including NPC
  interactions, past events, character knowledge, and unresolved threads.
- The Scribe remains usable on its own, without the Campaign Agent.

## Campaign Materials

Campaign plans and adventure modules should be human-readable and editable
as a collection of Markdown files. A campaign folder represents the
campaign as a book, with chapters that progress the story and contain one
or more adventures or NPC encounters. An adventure prepared for a game
session must be usable as a single file by the DM, without requiring other
campaign documents at the table. The campaign material is the source of
truth for planned story content; the Scribe's campaign record is the
source of truth for events that have occurred in play.

## Campaign Indexes

Every campaign keeps three indexes so the DM can find important things
quickly, in preparation and at the table:

| Index | File | Contains |
|---|---|---|
| Key NPCs | `npcs.md` | NPCs who matter to the story: allies, villains, quest givers, and anyone the party must meet again. |
| Key items | `items.md` | Magic items and artifacts that matter to the story. |
| Key locations | `locations.md` | Places that matter to the story: cities, dungeons, strongholds, and important sites. |

- Each entry has a name, a short description, its role in the story, and
  links to the sections where it appears. Full details, such as stat
  blocks, stay in those sections so adventures remain self-contained.
- Entries can link to maps; a location entry can link to its map.
- "Key" means important to the story. Minor NPCs and ordinary items stay
  in their adventures and are not indexed.
- In a running copy, each entry also has a status that Update Mode keeps
  current, such as an NPC's alive or dead status, who holds an item, or
  whether the party has visited a location.
- The indexes are the DM's view of the campaign, including secrets. They
  are separate from the Scribe's NPC and location registry, which records
  what the party has actually learned in play.
- Structural changes keep the indexes consistent: when a section moves or
  is dropped, the links in every index are updated, and entries that no
  longer appear anywhere are reported.

## Campaign File Structure

Each campaign section has its own Markdown file. Chapter folders group
their chapter outline with the adventures and standalone NPC encounters
that belong to it.

```text
<campaign-name>/
  campaign.md
  npcs.md
  items.md
  locations.md
  maps/
    <map-name>.png
  chapters/
    01-<chapter-name>/
      chapter.md
      adventures/
        01-<adventure-name>.md
      encounters/
        01-<encounter-name>.md
  sessions/                 # running copy only, written by the Scribe
    2026-10-20.md
  .scribe/                  # running copy only, the Scribe's data
  .gitignore
```

- `campaign.md` contains the campaign overview, central story arc, goals,
  and links to the chapters and the three indexes.
- `npcs.md`, `items.md`, and `locations.md` are the campaign indexes (see
  Campaign Indexes).
- Each `chapter.md` describes that chapter's place in the story and links
  to its adventures and encounters.
- Each adventure and standalone encounter is stored in its own Markdown
  file.
- An adventure file used for a session includes all details the DM needs
  to run its scenes and encounters. It may link to a standalone encounter
  file for reference, but must not require that file during the session.
- Number prefixes keep chapters and their contents in story order; names
  make the files easy to identify and navigate.
- All map files for the campaign are stored in the `maps/` folder. Campaign,
  chapter, and adventure files link to them with relative Markdown links.
- `sessions/` and `.scribe/` exist only in a running copy. The Campaign
  Agent reads `sessions/` and never writes to either.

Metadata conventions, including the master/running-copy marker, remain to
be decided.

## Maps

Maps are static images created and edited outside the Campaign Agent. The
DM edits a map in another tool and saves the new version into `maps/`. The
agent links maps to the right sections and uses them as campaign material.
The goal is an agent that uses maps while creating the campaign (level 4
below). The first version delivers level 1, and its design must not block
the later levels.

### Where maps belong

| Level | Maps | Examples |
|---|---|---|
| Campaign | One or more | World map, continent map |
| Chapter | Zero or more | Region map, city map |
| Adventure | Zero or more | Dungeon, encounter area |

- A map can be linked from more than one section, such as a city map used
  by a chapter and two of its adventures.
- Each map has a title, so a section with several maps stays readable.

### Formats

- Maps are common image formats that VS Code and the model can both
  display: PNG, JPEG, or WebP.
- Image formats the model cannot read directly, such as TIFF or SVG, are
  converted or reported with a clear message.
- PDF maps are not supported in the first VS Code version, because VS Code
  does not preview PDFs without an extension. The DM exports the map as an
  image instead.

### Version 1 requirements (level 1: store, link, view, and answer questions)

- The DM adds a map by saving it into `maps/`, for example by dragging it
  into the Explorer. The agent proposes the Markdown image link in the
  right section, using the normal review-before-accept step.
- Map links are image embeds, such as `![Smugglers' cove](../../maps/cove.png)`,
  so the map appears in the section's Markdown preview.
- The DM can open any map at full size beside the section it belongs to.
- Replacing a map file with an edited version under the same name keeps
  every link to it valid.
- The DM can link an existing map in `maps/` to another section without
  adding a copy of it.
- Map links stay valid when an adventure moves between chapters, and when a
  section is dropped the agent reports which maps are no longer linked
  instead of deleting them.
- When the DM asks about a map, the agent reads that map and answers using
  it together with the section's text. Maps are not sent to the model unless
  the conversation needs them, to keep cost down.
- Anything the agent reads from a map is treated as uncertain. The agent
  says when a label is unreadable or a detail is unclear rather than
  guessing.

### Roadmap toward level 4

| Level | What the agent does |
|---|---|
| 2. Index when attached | Reads a map once and proposes a text summary: labeled locations, connections, and notes on unclear areas. The DM reviews and corrects it, and later turns use the summary instead of resending the image. |
| 3. Consistency checks | Compares a section's maps with its text and reports gaps and mismatches, such as a numbered area with no description. |
| 4. Uses maps while creating | Writes location keys, places encounters, and describes travel routes based on the reviewed map summaries. |

- A reviewed map summary is the agent's working knowledge of that map.
  Unreviewed readings must not flow into campaign text.
- When the DM replaces a map with an edited version, its summary is marked
  out of date until it is reviewed again.
- Large or detailed maps may need to be split into tiles for the model to
  read small labels. Whether this is needed is decided by testing with real
  campaign maps.
- Where map summaries are stored, for example a Markdown file next to each
  map in `maps/`, is decided when level 2 is designed.

### Later: deleting maps

- The DM can delete a map from `maps/`. Before deleting, the agent lists
  every section that links to it and proposes removing those links, so no
  broken references remain.
- Unlinked maps, such as those left behind when a section is dropped, are
  easy to find so the DM can decide whether to delete them.

## Goals

Add campaign goals here, such as desired tone, themes, pacing, or the kind
of experience the players should have.

## Non-goals

- Replacing the DM's authority or running the game at the table.
- Replacing the Scribe's record of events that have actually happened.
- A custom VS Code extension. VS Code's Explorer, Markdown preview, and
  split editors cover the first version; a dedicated extension is
  reconsidered only if daily use shows a need it cannot meet.
- Editing or annotating maps. Maps are static images edited in other tools.

## Open Questions

- What campaign details should be shared across all adventure modules?
- What format should the DM and Scribe use to review a prepared module?
- How are adventures that have already been played marked, so Update Mode
  revises only what lies ahead?
- Should the Scribe's database in `.scribe/` be committed with the
  campaign, or excluded and backed up separately?
