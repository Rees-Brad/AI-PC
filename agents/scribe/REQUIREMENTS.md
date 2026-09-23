# Scribe Agent Requirements

## Purpose

The Scribe is the campaign's memory. It listens to the table, maintains a
running record of what has happened, and serves that record back to the
humans and to the other AI agents.

It is not a player. It has no character sheet, takes no turns, rolls no
dice, and never participates in the fiction. Where the PC agent is a
participant, the Scribe is an observer.

### Useful on its own

The Scribe stands alone. At a table of entirely human players, with no
other AI agents present, it still earns its place: it captures campaign
history that would otherwise live in someone's notebook or nobody's, and
it answers the questions tables actually ask — "who was that innkeeper?",
"what did we agree to do for the guild?", "where did we leave off?"

No part of the Scribe assumes an AI PC, DM, or NPC agent exists.

### Bootstraps the other agents

The same record is what makes the other agents possible. A PC agent
joining an established campaign — taking over a departing player's
character, or being added mid-campaign — gets its history, relationships,
and open threads from the Scribe's record rather than from a human having
to brief it (see the PC agent's Character Creation, option 3).

The dependency runs one way: PC agents need the Scribe, the Scribe needs
nothing. For that reason the Scribe is built and shipped **first** — it
can be proven at a real table, on its own, before anything depends on it.

## Interfaces

### 1. Discord voice channel (primary input)

The Scribe joins the campaign's voice channel as its own Discord bot and
transcribes the table's audio via speech-to-text.

- **Listen-only.** The Scribe never speaks into the voice channel. It has
  no TTS output and never interrupts play.
- **Speaker attribution.** Discord provides per-user audio streams, so the
  Scribe records who said what — DM, human players, and AI PC bots alike.
- Session boundaries match the PC agent's definition: a session starts
  when the Scribe joins the voice channel and ends when it leaves.

### 2. Discord text/slash commands (query + control)

Silent by default, but answers when asked. All responses are text in the
channel — never voice.

- `/recap [session]` — the recap for the last session, or a named one.
- `/who <name>` — what's known about an NPC.
- `/where <name>` — what's known about a location.
- `/threads` — current open plot threads and unresolved hooks.
- `/knows <event>` — which characters are aware of an event, and whether
  each knows it firsthand or secondhand (see Awareness queries).
- `/note <text>` — DM-only; add a record by hand.
- `/correct <text>` — DM-only; correct the record (see DM authority).

### 3. Campaign database (output to other agents)

The Scribe owns a campaign-level database and is its **only writer**.

- PC agents (and later DM/NPC agents) get **read-only** access to it, so
  they can pull campaign continuity into their own context.
- Each consuming agent is configured with the path to this database (e.g.
  `AI_PC_CAMPAIGN_DB_PATH` in a PC instance's `.env`).
- This database is the one piece of storage shared across agents in a
  campaign. Each agent's own character/private state stays in its own
  instance database.

### 4. Out of scope for v1

Noted for later, not built now: cross-campaign memory, exporting the
campaign record to external tools (wikis, VTTs), summarizing from
recordings after the fact rather than live, and any non-Discord input.

## What the Scribe Maintains

### Session recaps

A narrative summary of each session — what the party did, what changed,
what was decided. This is the primary artifact other agents read for
continuity.

### Plot threads and open questions

A running list of unresolved hooks, accepted quests, outstanding
mysteries, and promises the party has made. Threads are opened, updated,
and closed as sessions progress, so the list reflects what is actually
still live rather than everything ever mentioned.

### NPC and location registry

A running index of NPCs met, places visited, and factions encountered,
with what the party currently knows about each and where they last came
up.

## Record Keeping

### Rolling, incremental updates

Records are updated continuously during a session, not only at the end. A
current recap always exists, even mid-session, so a crash or an early
disconnect never loses the whole session's memory. The end of a session
finalizes the recap rather than being the first time one is written.

### Transcript retention

The raw speech-to-text output is a **working buffer for the current
session only**. Once that session's recap is finalized, the transcript is
discarded.

The durable record is the summarized material — recaps, threads, and the
registry — not a permanent archive of everything anyone said at the
table.

### DM authority over the record

The DM can correct, amend, or remove anything the Scribe has recorded,
and the Scribe accepts the correction without argument. As with the PC
agent, the DM's ruling is absolute: the Scribe never defends its previous
version of events.

## Behavior Requirements

### Silent observer

The Scribe does not volunteer commentary, does not narrate, and does not
inject itself into scenes. It produces output only when queried, or when
writing to its own records.

### Records, does not invent

The Scribe summarizes what actually happened at the table. Where
something was ambiguous or inaudible, it records the uncertainty rather
than filling the gap with a plausible guess.

### Shared record, no per-character filtering

The Scribe keeps one party-wide record and does not produce per-character
filtered recaps. Recaps may therefore contain things a given character did
not personally witness.

Consuming agents are responsible for not acting on knowledge their
character never learned — see the PC agent's requirements. The Scribe's
job is an accurate record and an honest answer about who knows what, not
enforcing in-fiction knowledge boundaries on anyone's behalf.

### Awareness queries

Although recaps aren't filtered, the Scribe can answer, on demand, which
characters are aware of a given event — and for each, whether they know
it **firsthand** (present for it) or **secondhand** (told about it
later).

- Awareness is **inferred from the record** — who was in the scene, who
  spoke, who was addressed, and who was later told. It is a judgment
  call, not a mechanical presence check, so it can be wrong; the DM can
  correct it like any other record.
- Available to **both humans and agents**: the table asks via `/knows`,
  and consuming agents can query the same capability through the campaign
  database when unsure whether their character was present for something.

This is what makes the PC agents' self-policing practical: an agent that
doesn't know whether its character witnessed an event can ask, rather
than guess.

#### Regrouping implies sharing

Tables routinely hand-wave the catch-up — "we fill them in over
breakfast," or nothing said at all. The Scribe assumes it happened: when
a split party regroups, characters who weren't present become aware
**secondhand** of what the others found, without anyone having to
roleplay the recounting.

- **Material information transfers** — what was discovered, who was met,
  what was decided, what's now planned. Incidental colour and private
  character moments do not.
- **Concealment is sticky.** Anything a character explicitly hid from the
  party, or that the DM marked private, does not transfer on regrouping.
  It stays unknown until it is actually shared on screen. A secret kept
  deliberately is usually the point of the scene, and the Scribe never
  dissolves one by inference.
- As with all awareness inference, the DM can correct any of this.

### Access control

- Recaps, threads, and registry lookups are open to anyone at the table.
- Records the DM explicitly marks private (DM notes, prep material, asides
  recorded via `/note`) are visible only to the DM and are never exposed
  to other agents through the campaign database.

## Configuration & Secrets

Identical in spirit to the PC agent: no credentials, API keys, or tokens
are ever committed to the repo. All secrets come from environment
variables / a local `.env` file in the instance's own directory.

The Scribe has its own Anthropic API key and its own Discord bot
token/application, separate from every PC agent's.

## Startup & File Discovery

**Hosting** — Like the PC agent, the Scribe runs on separate, always-on
infrastructure and is never assumed to be running on a human player's
device. Players interact with it only through the Discord client.

**Instance directory** — The Scribe runs from its own working directory,
outside the repository checkout, holding its `.env`, the campaign
database it owns, and any other data it needs.

**One per campaign** — Exactly one Scribe deployment serves a campaign,
in contrast to PC agents, which are one per character.

## Goals

- **Reliable continuity** — the table (and the other agents) can trust
  that what happened last session is recorded accurately and is available
  next session.
- **Zero table friction** — the Scribe costs the table nothing in
  attention. It never interrupts, never asks for clarification mid-scene,
  and requires no one to remember to feed it anything.
- **Useful recall, not bulk archive** — answering "who was that
  innkeeper?" matters more than storing every word spoken.
- **Cheap to run** — summarization is background work and should use
  inexpensive models; it should not scale in cost with every spoken turn
  the way live play does.

## Non-goals (v1)

- Participating in the fiction in any way.
- Speaking aloud in the voice channel.
- Per-character filtered recaps (awareness can be *queried*, but recaps
  themselves are never tailored per character).
- Permanent transcript archives.
- Serving more than one campaign from a single deployment.
