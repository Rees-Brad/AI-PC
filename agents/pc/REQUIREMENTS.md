# AI-PC Requirements

## Purpose

AI-PC is an AI-backed Dungeons & Dragons 5e Player Character. It is a full
autonomous player: it owns its own character sheet, rolls its own dice, and
applies 5e rules itself — not just an in-fiction chat companion that a human
still has to referee and track state for.

## Interfaces

### 1. Discord voice channel (primary)

The "at the table" interface. The AI PC joins a Discord voice channel,
listens when activated, and speaks its character's lines back via
text-to-speech.

- Activation is explicit (`/pc listen`) in v1 — not always-on ambient
  listening. Ambient wake-word activation is a v2 stretch goal.
- Output is synthesized speech played into the voice channel, in the
  character's voice.

### 2. Discord text/slash commands (secondary — control + query)

- `/say` — text-only fallback for the AI's turn (also the first interface
  built, before voice exists).
- `/sheet` — view the character sheet.
- `/sheet-pdf` — DM-only; generates the current character sheet as a PDF
  and posts it as an attachment in the channel (see Command access
  control below).
- `/inventory` — view inventory.
- `/roll` — request a manual roll.
- `/rest` — trigger a short/long rest.
- Admin/override commands (manual HP or inventory edits, session reset,
  forcing a ruling) — restricted, see Command access control below.

### 3. Channel & server configuration

Each deployment is configured (via its `.env`, consistent with
Configuration & Secrets) with the specific Discord server and channels it
operates in — there is no dynamic discovery:

- **Server** — one deployment is invited to, and operates in, exactly one
  Discord server (guild) for its campaign.
- **Voice channel** — a fixed voice channel ID is configured (e.g.
  `AI_PC_VOICE_CHANNEL_ID`); the AI PC always joins that same channel when
  activated (`/pc listen`), regardless of who invokes the command or where
  they currently are.
- **Text channel** — slash commands (`/sheet`, `/inventory`, `/roll`,
  `/rest`, `/sheet-pdf`, admin commands) are only recognized in one
  designated text channel for that campaign (e.g. `AI_PC_TEXT_CHANNEL_ID`);
  commands issued elsewhere are ignored or rejected.

### 4. Command-line interface (testing only)

A local CLI, formalizing the existing `scripts/chat_repl.py` and
`scripts/create_character.py` dev scripts, for exercising the AI PC
without Discord running. Not a table/production interface — Discord voice
remains the primary interface for actual gameplay.

- Supports the full command surface available in Discord — conversational
  chat plus CLI equivalents of `/sheet`, `/inventory`, `/roll`, `/rest`,
  and admin/override commands — so any gameplay path can be exercised
  without Discord.
- Reads and writes the same character database as Discord sessions (same
  `AI_PC_DB_PATH`), so it doubles as a way to inspect/debug a live
  campaign character's actual state, not just a disposable test character.

### 5. Out of scope for v1

Noted for a future generalization, not built now: VTT platform integration
(Roll20, Foundry), non-Discord text chat, other game systems besides D&D 5e.


## Character Creation

### 1. The AI creates a character (primary)

The AI is free to create the character. The DM may constrain any of the
following before creation starts; anything the DM doesn't constrain is the
AI's call:

- **Class** — one of three modes:
  1. **DM specifies** — the DM tells the AI exactly which class to play;
     this overrides the other two modes.
  2. **AI free choice** — absent a DM specification, the AI picks
     whatever class it wants.
  3. **AI waits and complements** — absent a DM specification, the AI
     instead defers its choice until every other party member has
     declared their class, then picks something that rounds out the
     party's composition (e.g. a healer if none exists).

     Whether the AI uses (2) or (3) when the DM hasn't specified a class
     is the AI's own judgment call.
- **Alignment** — DM may restrict to good, evil, or a specific alignment.
- **Race** — DM may limit race options.
- **Gender** — DM may limit gender options.
- **Starting level** — DM sets the party's starting level.
- **Ability scores** — DM sets the generation method used at the table
  (standard array, point buy, or rolled).
- **Background/backstory** — free to the AI unless the DM specifies
  otherwise.
- **Starting equipment** — standard class equipment unless the DM
  specifies otherwise.
- **Name** — free to the AI; DM may request a change before the campaign
  starts.

Where the DM sets no constraint, the AI decides and presents the finished
sheet to the DM for approval before session zero — except when the AI
uses the "waits and complements" class mode above, where the class choice
(and therefore the finished sheet) may not be finalized until every other
party member has declared theirs, which can be as late as session zero
itself. In that case, DM approval happens before the AI's first turn
rather than strictly before session zero starts.

### 2. DM provides a pre-made character sheet (secondary)

The AI uses the pre-made character sheet provided by the DM as-is.

- The AI can suggest changes (e.g. background story, race, gender,
  starting equipment), but the DM has final say.
- Once the campaign starts, the AI is free to make the character its own
  in personality and roleplay, even though the DM controls the sheet's
  mechanics.

### 3. The AI assumes an existing character when a party member leaves (option)

The AI is given the existing character sheet and a history of the
campaign (session summaries/logs), and takes over the character at its
current state — level, HP, inventory, and established backstory
unchanged.

- The AI infers personality/voice from the campaign history where it's
  already established, and makes a reasonable judgment call to fill in
  anything that isn't.
- As with option 2, the DM has final say on any changes the AI proposes
  to the character going forward.

### 4. Discord identity registration

Until a character name exists, the AI PC connects to Discord under a
generic placeholder name (its Discord Application's configured default,
e.g. "AI PC (unnamed)"). Once the character's name is finalized — via any
of the character-creation paths above — the agent renames its Discord bot
identity to match. This is a one-time step done as part of completing
character creation, not repeated on every startup.

**Uniqueness** — Before finalizing the name, the agent checks the names of
other PC agent bots already present in the server/voice channel and avoids
colliding with an existing character's name. A collision is handled the
same way any other AI-decided detail is: the AI revises its choice (or
flags it for the DM), consistent with the DM-approval step already
required before session zero.

## Character Persona
Persona includes
- personallity
- speach pattern / accent
- rather the character is aggressive in combat or more hestiant

### 1. The AI is free to define persona (primary)
The AI defines the persona of the character. Persona choices, especially
combat temperament, should be informed by the character's class and
mechanical role — e.g. considering what fits a tank vs. a squishy caster —
without being dictated by it: a tank could just as reasonably be a
reckless front-liner or a calm, disciplined guardian. The class is context
for the decision, not a fixed answer.

### 2. The DM defines the persona (secondary)
The DM will define the persona of teh character, how they should act and function in the group.  This is more of when the PC is in a supporting role and not one of the main characters.



## Behavior Requirements

### In-character default, narrow OOC exception

The AI PC speaks and acts in-character by default. It may break character
only when genuinely blocked from acting — e.g. an unstated DC or an
ambiguous target — in which case it prefixes the line with `(OOC)` and asks
a short clarifying question, then returns to character. It does not use OOC
as a general hedge; if it can make a reasonable in-fiction judgment call, it
does that instead of asking.

### DM authority is absolute and silent

If the DM's ruling conflicts with what the rules engine computed (e.g. the
DM overrules a spell's effect), the AI PC updates its state to match the
DM's ruling and moves on in-character with no pushback and no explanation of
its own prior calculation. The rules engine exists to keep the AI's default
play consistent and fast — never to contest the DM.

### No metagaming from campaign memory

The Scribe agent keeps one party-wide record and does not filter it per
character (see `agents/scribe/REQUIREMENTS.md`). Its recaps may therefore
describe events the AI PC's character never personally witnessed — a DM
aside, a scene the party split away from, another character's private
dealings.

The AI PC is responsible for policing this itself: it may use campaign
memory to stay consistent, but it acts only on what its character
plausibly knows.

When it is unsure whether its character witnessed something, it asks the
Scribe rather than guessing — the Scribe answers which characters are
aware of an event and whether they know it firsthand or secondhand. If
that answer is unavailable or inconclusive, the AI PC plays as though its
character does not know.

### Command access control

- Read/query commands (`/sheet`, `/inventory`) are open to anyone at the
  table.
- `/sheet-pdf` is read-only but restricted to the DM specifically (not
  open to other players, and not extended to the owner role by default).
- Commands that mutate state outside the normal tool-driven flow (manual
  HP/inventory edits, session reset, forcing a ruling) are restricted to two
  roles, checked against configured Discord user IDs:
  - the **DM**
  - the AI PC's **owner** (the human who set up and plays alongside this
    character)

## Session & State Persistence

**Save triggers** — State (HP, inventory, conditions, spell slots) commits
to the database at the end of each in-game turn/action group (e.g., an
attack roll plus its damage commit together), not on every individual
field change or purely on a timer.

**Session boundaries** — A session starts when the AI PC joins the Discord
voice channel (or `/pc listen` begins) and ends on disconnect/leave. This
is the unit used for session logs and summaries.

**Crash recovery** — On restart after a crash or disconnect mid-session,
the AI PC automatically reloads character state as of the last commit and
reconnects to the last known voice channel, resuming without requiring
DM/owner intervention.

**Continuity / summarization** — Long-term campaign memory is produced by
the Scribe agent (`agents/scribe/`), which ships **before** the PC agent —
it has no dependencies of its own and is useful at a human-only table, so
it is in place and proven before any PC agent needs continuity from it. Scribe owns a campaign-level database that the PC agent has **read-only**
access to; Scribe writes session recaps there and the PC agent reads them.
Each PC instance is configured with the path to that database (e.g.
`AI_PC_CAMPAIGN_DB_PATH`). This is the one exception to Multi-instance
isolation below — no direct agent-to-agent call is needed.
Each session's LLM context is built from all prior session summaries (from
Scribe) plus the raw session-log tail of the current, in-progress session.
The PC agent does not generate its own summaries.

**Durability** — No backup/export requirement in v1 beyond the SQLite file
itself; the DM/owner is responsible for their own backups if desired.

## Configuration & Secrets

No credentials, API keys, or tokens (Anthropic API key, Discord bot token,
etc.) are ever committed to the repo. All secrets are supplied via
environment variables / a local `.env` file (gitignored), following the
pattern in `.env.example`.

**Multi-instance isolation** — A campaign may run more than one PC agent
deployment simultaneously (one per AI-played character). Each deployment
is fully self-contained: its own Anthropic API key, own Discord bot
token/application, own database file, and own session memory/state. No
configuration, credentials, or character storage is shared between
instances.

The single exception is the campaign-level database owned by the Scribe
agent (see Continuity / summarization above), which every PC agent in the
campaign may read — but never write. Character state always stays private
to its own instance.

## Startup & File Discovery

**Hosting** — The AI PC agent process runs on separate, always-on
infrastructure (e.g. a home server, VPS, or a desktop left running) — it
is never assumed to be a human player's own device. Players interact with
it purely through the Discord client on whatever device they use (phone,
tablet, desktop); no player needs to install, configure, or run anything
locally to play.

The owner role (see Command access control) is responsible for starting
and maintaining that hosting, but the machine they start/manage the agent
on can be entirely different from the device they personally connect to
Discord with to actually play — e.g. the owner starts the process on a
home server or VPS, then joins the session from their phone or tablet
like any other player.

Each AI PC deployment runs from its own working directory, which is the
single source of truth for that instance's files: its `.env` (API keys,
tokens, per-instance settings), its SQLite database, and any
character-specific data (e.g. voice model, persona notes) under `data/`.
There is no config-directory flag or environment variable for locating
these — an instance is started with its working directory set to that
instance's directory (e.g. `cd ~/ai-pc-instances/grog/ && ai-pc`, or a
process manager's working-directory setting pointed there).

**Instance directories live outside the repository checkout** (e.g. under
the home directory, not inside the cloned `AI-PC/` tree). This is a
structural guarantee, not just a `.gitignore` convention: a secret or DB
file that never lives inside the repo working tree cannot be accidentally
committed, regardless of `.gitignore` correctness.

Running multiple PCs for one campaign (see Multi-instance isolation above)
means running multiple such directories side by side, each launched with
a plain `ai-pc` invocation in its own directory. No built-in orchestration
(compose file, systemd templates, etc.) is provided in v1 — the DM/owner
manages each process themselves.

## Goals

- **Table experience quality** — the AI PC should feel like a real, present
  player at the table: natural conversational pacing and genuine
  in-character reactions, not a monotone tool executing commands.
- **Rules accuracy & consistency** — 5e math (attack rolls, damage, spell
  effects, saving throws) is reliably correct so the DM never has to
  double-check the AI's own rolls.
- **Campaign continuity** — the AI PC remembers past sessions: its own
  character growth, relationships with other PCs/NPCs, and ongoing plot
  threads, and lets that history inform how it plays in future sessions.
- **Low operational friction** — easy for the DM/owner to start and run;
  recovers gracefully from disconnects or crashes without losing
  character state.
- **Player safety / table conduct** — the AI PC never kills or
  permanently maims another player's character, even when its own
  character's alignment or motivation (e.g. an evil-aligned PC) would
  in-fiction justify it. This guardrail holds even in tension with
  staying strictly in-character — protecting the group's fun overrides
  in-fiction consistency here. NPCs/monsters are unaffected; normal
  combat rules apply against them.
- **OOC communication when needed** — the AI PC can step out of character
  for brief clarifications (see Behavior Requirements) so genuine
  ambiguity doesn't stall the table.

## Non-goals (v1)

- Multi-PC support within a single agent process (one AI PC per
  deployment/process — see Configuration & Secrets for running several
  deployments together in one campaign).
- Systems other than D&D 5e.
- Always-on ambient voice activation.
