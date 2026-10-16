# Campaign Agent Requirements

## Purpose

The Campaign Agent helps the DM create and maintain a long-running campaign.
It assists in developing the campaign's central story arc and a collection of adventure
modules, then helps prepare each module for the party's next game night.

The campaign should have direction without forcing the players down a
single path. Side quests, alternate leads, and meaningful consequences
give the players room to choose what matters to them.

A campaign at a minimum must have:
  1. A goal (objective)
  2. One adventure with at least one encounter

The Campaign Agent works with the other agents to continually update
future modules to keep the story progressing.
A useful workflow could be:

1. Campaign Agent builds the central arc, setting, factions, key NPCs, and a collection of adventure modules. Each module can have multiple hooks, outcomes, and ways to connect back to the larger story.
2. Before game night, the Campaign Agent selects and adapts the next module based on where the characters are and what they’ve chosen to pursue.
3. DM Agent reviews it for playability and whether its events still fit the larger arc.
4. Scribe Agent checks campaign records for continuity: NPC relationships, unresolved events, character knowledge, and consequences that the draft might contradict.
5. Campaign Agent incorporates those reviews and offers side quests or alternate leads that feel connected to the world, while keeping the main arc available rather than compulsory.

## Operating Modes

The Campaign Agent operates in one of three modes:
  1. Reviewer Mode
  2. Campaign Creation Mode
  3. Update Mode

Each mode is defined in the Operating Modes Details section


## User Interface

The first version provides a simple visual interface beyond a command-line
program. It is a local browser-based application for the user and Campaign
Agent to work together; the Campaign Agent does not need to join a Discord
channel.

- The user selects an operating mode and, as appropriate, a campaign
  directory, campaign folder, or review/starting document through the
  interface.
- The selected campaign directory and campaign folder are visible and
  selectable in Creation and Update modes. Selecting an existing campaign
  continues work from its saved Markdown.
- The user can revise an existing campaign's structure during Creation or
  Update: add or drop chapters and adventures, or move adventures between
  chapters. Proposals show the affected files and updated references before
  the user approves the changes.
- Reviewer and Creation modes accept supported text documents and PDFs
  with selectable text. The interface communicates that scanned PDFs
  require OCR and are not supported.
- The main interaction is an ongoing natural-language conversation. The
  user can ask follow-up questions and respond to the agent without
  entering a separate command for every turn.
- The interface displays the conversation and any campaign material the
  agent is discussing or proposing.
- In Campaign Creation and Update modes, the agent presents proposed file
  additions or edits for the user to review before they are applied.
- Reviewer Mode remains read-only and does not offer to write campaign
  documents.
- In Creation and Update modes, the user can attach maps to the campaign, a
  chapter, or an adventure, and can view a section's maps alongside its
  Markdown. See Maps.

## Operating Modes Details

### 1. Reviewer Mode

The user provides a campaign document or other campaign material for
review. The Campaign Agent analyzes only the supplied material and returns
feedback and suggestions for the user to consider.

- The agent may identify strengths, unclear points, inconsistencies,
  potential risks, and opportunities for development.
- Suggestions are advisory; the user decides whether to accept or apply
  them.
- The agent does not create, edit, or rewrite campaign documents in this
  mode. It returns its review as a response, not as a new campaign file.
- The agent does not assume details that are absent from the supplied
  material. It identifies missing context or uncertainty where that
  affects its feedback.
- The user can provide a text document or a PDF with selectable text for
  review. Scanned PDFs without an OCR text layer are not supported.

### 2. Campaign Creation Mode

The user provides an initial story or plot description, along with any
campaign goals and objectives. The user and Campaign Agent then work
together to develop the idea into a campaign.

- The creation of a campaign could take multiple interaction sessions.
  The Agent will save checkpoints to allow the process to continue at a future session.
  This means that the careted files could be empty
- As a campaign is being created various parts can be moved across chapters or adventures. 
  The Agent needs to be able to allow large portions to be moved and the asses the story arc 
  for breaks or issues. 
- The user can optionally provide starting notes or a source document to
  inform campaign creation. Supported documents include text files and PDFs
  with selectable text; scanned PDFs without an OCR text layer are not
  supported.
- The user can choose the directory in which campaign folders are listed
  and created.
- The user can resume creation by selecting an existing campaign. The agent
  uses that campaign's saved Markdown as context, and approved proposals are
  written back to the selected campaign folder.
- The agent asks questions and offers options to help flesh out the
  premise, central story arc, setting, themes, and intended player
  experience. The user guides the direction and makes the final decisions.
- The agent supports player choice by developing optional paths, side
  quests, and meaningful alternatives to the main story route.
- As the campaign takes shape, the agent creates a campaign folder
  containing human-readable Markdown documents.
- The campaign is organized like a book: chapters progress the story,
  and each chapter contains one or more adventures or NPC encounters.
- Each campaign section is its own Markdown file, including the campaign
  overview, chapters, adventures, and standalone NPC encounters.
- When asked to initialize a campaign scaffold, the agent proposes a
  `campaign.md`, a `chapter.md` for each chapter, and separate Markdown files
  for each adventure and standalone encounter. It does not combine the whole
  campaign into one file.
- The campaign structure is provisional and can change as development
  continues. The user can add or drop chapters and adventures, and move an
  adventure from one chapter to another.
- When proposing a structural change, the agent updates the affected chapter
  and campaign indexes so they match the new structure. Dropped or moved
  sections must not leave stale or broken references in the active campaign.
- Structural file changes are presented for user review before they are
  applied; existing material is not silently discarded.
- An adventure intended for a game session is self-contained: it includes
  the relevant background, scenes, NPCs, encounters, and running details
  the DM needs for that session. References to other campaign files may be
  included for broader context, but the DM does not need to open them to
  run the session.
- The agent keeps planned events distinct from events that have actually
  happened in play; the Scribe remains the source of truth for the latter.

### 3. Update Mode

After each session, or at the latest before the next session, the Campaign
Agent works with the user and consults the Scribe to update the remaining
campaign. The Scribe provides the record of what happened; the user and DM
provide corrections, rulings, and direction for what happens next.

- Review the session record for completed events, character decisions,
  NPC interactions, and changes to open story threads.
- Calculate and track experience points earned from fights, check whether
  characters qualify to level up under the campaign's advancement rules,
  and surface the results for user/DM confirmation.
- Reassess planned encounter difficulty using the characters' current
  levels and capabilities, and adjust future encounters where needed.
- Revise the remaining adventures, encounters, and story arc to reflect
  the session's outcomes and NPC interactions. Preserve continuity while
  allowing the story to change in response to player choices.
- Update the relevant campaign Markdown files without rewriting the
  Scribe's record of events that actually occurred.
- The DM has final authority over XP awards, level advancement, encounter
  rulings, and campaign changes.



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

### DM Agent

The DM reviews a prepared adventure for playability and fit with the
campaign's story arc. The Campaign Agent can revise the adventure in
response to that review. The DM remains the final authority over what
happens at the table.

### Scribe Agent

The Scribe checks proposed material against the campaign record, including
NPC interactions, past events, character knowledge, and unresolved plot
threads. Its record describes what has happened; campaign plans describe
what may happen. The Campaign Agent uses Scribe feedback to keep new
material consistent with the record.

## Campaign Materials

Campaign plans and adventure modules should be human-readable and editable
as a collection of Markdown files. A campaign folder represents the
campaign as a book, with chapters that progress the story and contain one
or more adventures or NPC encounters. An adventure prepared for a game
session must be usable as a single file by the DM, without requiring other
campaign documents at the table. The campaign material is the source of
truth for planned story content; the Scribe's campaign record is the
source of truth for events that have occurred in play.

## Campaign File Structure

Each campaign section has its own Markdown file. Chapter folders group
their chapter outline with the adventures and standalone NPC encounters
that belong to it.

```text
<campaign-name>/
  campaign.md
  maps/
    <map-name>.jpg
    <map-name>.pdf
  chapters/
    01-<chapter-name>/
      chapter.md
      adventures/
        01-<adventure-name>.md
      encounters/
        01-<encounter-name>.md
```

- `campaign.md` contains the campaign overview, central story arc, goals,
  and links to the chapters.
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

Metadata conventions and how agents read or update campaign files remain
to be decided.

## Maps

Maps are created outside the Campaign Agent. The agent stores them, links
them to the right sections, and uses them as campaign material. The goal is
an agent that uses maps while creating the campaign (level 4 below). The
first version delivers level 1, and its design must not block the later
levels.

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

- Maps can be common image formats (such as JPEG, PNG, or WebP) or PDF.
- Image formats the model cannot read directly, such as TIFF or SVG, are
  converted or rejected with a clear message.
- Map PDFs are read as images, not as extracted text, since a map's content
  is mostly visual.

### Version 1 requirements (level 1: store, link, and answer questions)

- The user can attach a map to the campaign, a chapter, or an adventure.
  The agent copies the file into `maps/` and proposes the Markdown link in
  the section, using the normal review-before-apply step.
- The user can link an existing map in `maps/` to another section without
  adding a copy of it.
- Map links stay valid when an adventure moves between chapters, and when a
  section is dropped the agent reports which maps are no longer linked
  instead of deleting them.
- The interface shows a section's maps with its Markdown and lets the user
  open a map at full size.
- When the user asks about a map, the agent reads that map and answers using
  it together with the section's text. Maps are not sent to the model unless
  the conversation needs them, to keep cost down.
- Anything the agent reads from a map is treated as uncertain. The agent
  says when a label is unreadable or a detail is unclear rather than
  guessing.

### Roadmap toward level 4

| Level | What the agent does |
|---|---|
| 2. Index when attached | Reads a map once and proposes a text summary: labeled locations, connections, and notes on unclear areas. The user reviews and corrects it, and later turns use the summary instead of resending the image. |
| 3. Consistency checks | Compares a section's maps with its text and reports gaps and mismatches, such as a numbered area with no description. |
| 4. Uses maps while creating | Writes location keys, places encounters, and describes travel routes based on the reviewed map summaries. |

- A reviewed map summary is the agent's working knowledge of that map.
  Unreviewed readings must not flow into campaign text.
- Large or detailed maps may need to be split into tiles for the model to
  read small labels. Whether this is needed is decided by testing with real
  campaign maps.
- Where map summaries are stored, for example a Markdown file next to each
  map in `maps/`, is decided when level 2 is designed.

### Later: deleting maps

- The user can delete a map from `maps/`. Before deleting, the agent lists
  every section that links to it and proposes removing those links, so no
  broken references remain. The deletion and link removals go through the
  normal review-before-apply step.
- Unlinked maps, such as those left behind when a section is dropped, are
  easy to find so the user can decide whether to delete them.

## Goals

Add campaign goals here, such as desired tone, themes, pacing, or the kind
of experience the players should have.

## Non-goals

- Replacing the DM's authority or running the game at the table.
- Replacing the Scribe's record of events that have actually happened.

## Open Questions

- What campaign details should be shared across all adventure modules?
- How should the Campaign Agent incorporate player choices that move the
  story away from its original plan?
- What format should the DM and Scribe use to review a prepared module?
- Should the agent edit campaign files directly, or propose revisions for
  DM approval?
