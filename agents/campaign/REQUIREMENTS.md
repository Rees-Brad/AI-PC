# Campaign Agent Requirements

## Purpose

The Campaign Agent helps the DM create and maintain a long-running campaign.
It develops the campaign's central story arc and a collection of adventure
modules, then helps prepare each module for the party's next game night.

The campaign should have direction without forcing the players down a
single path. Side quests, alternate leads, and meaningful consequences
give the players room to choose what matters to them.

The Campaign Agent works with the other agents to continually update
future modules to keep the story progressing.
A useful workflow could be:

1. Campaign Agent builds the central arc, setting, factions, key NPCs, and a collection of adventure modules. Each module can have multiple hooks, outcomes, and ways to connect back to the larger story.
2. Before game night, the Campaign Agent selects and adapts the next module based on where the characters are and what they’ve chosen to pursue.
3. DM Agent reviews it for playability and whether its events still fit the larger arc.
4. Scribe Agent checks campaign records for continuity: NPC relationships, unresolved events, character knowledge, and consequences that the draft might contradict.
5. Campaign Agent incorporates those reviews and offers side quests or alternate leads that feel connected to the world, while keeping the main arc available rather than compulsory.

## Operating Modes

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

### 2. Campaign Creation Mode

The user provides an initial story or plot description, along with any
campaign goals and objectives. The user and Campaign Agent then work
together to develop the idea into a campaign.

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

## User Interface

The first version provides a simple visual interface beyond a command-line
program. It is a local browser-based application for the user and Campaign
Agent to work together; the Campaign Agent does not need to join a Discord
channel.

- The user selects an operating mode and the campaign folder or review
  document through the interface.
- The main interaction is an ongoing natural-language conversation. The
  user can ask follow-up questions and respond to the agent without
  entering a separate command for every turn.
- The interface displays the conversation and any campaign material the
  agent is discussing or proposing.
- In Campaign Creation and Update modes, the agent presents proposed file
  additions or edits for the user to review before they are applied.
- Reviewer Mode remains read-only and does not offer to write campaign
  documents.

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

Metadata conventions and how agents read or update campaign files remain
to be decided.

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