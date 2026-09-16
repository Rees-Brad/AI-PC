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
- `/inventory` — view inventory.
- `/roll` — request a manual roll.
- `/rest` — trigger a short/long rest.
- Admin/override commands (manual HP or inventory edits, session reset,
  forcing a ruling) — restricted, see Command access control below.

### 3. Out of scope for v1

Noted for a future generalization, not built now: VTT platform integration
(Roll20, Foundry), non-Discord text chat, other game systems besides D&D 5e.


## Character Creation

### 1. The AI creates a character (primary)

The AI is free to create the character. The DM may constrain any of the
following before creation starts; anything the DM doesn't constrain is the
AI's call:

- **Class** — DM may suggest or restrict based on party needs (e.g. "we
  need a healer").
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
sheet to the DM for approval before session zero.

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

## Character Persona

### 1. The AI is free to define persona




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

### Command access control

- Read/query commands (`/sheet`, `/inventory`) are open to anyone at the
  table.
- Commands that mutate state outside the normal tool-driven flow (manual
  HP/inventory edits, session reset, forcing a ruling) are restricted to two
  roles, checked against configured Discord user IDs:
  - the **DM**
  - the AI PC's **owner** (the human who set up and plays alongside this
    character)

## Goals 




## Non-goals (v1)

- Multi-PC support (one AI PC per deployment for now).
- Systems other than D&D 5e.
- Always-on ambient voice activation.
