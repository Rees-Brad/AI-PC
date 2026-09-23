# AI PC Agent

The AI-backed D&D 5e Player Character agent. See
[REQUIREMENTS.md](REQUIREMENTS.md) for the full interface and behavior
spec this agent is being built against.

## Status

What actually works today: character creation and text-only chat via the
CLI scripts below, backed by a real Anthropic API call and a local SQLite
database. The Discord bot (voice + slash commands), PDF sheet export, and
admin/override commands described in REQUIREMENTS.md are not implemented
yet.

## Prerequisites

- Python 3.10+
- An Anthropic API key

## Setup

1. From the repo root, install the packages as editable installs (order
   matters — `shared` first):

   ```bash
   pip install -e ./shared -e './agents/pc[dev]'
   ```

   (Use a venv if you have one available; `pip install --user` works too
   if `python3-venv` isn't installed on your system.)

2. Create an instance directory **outside this repo checkout**. This
   holds your `.env` (secrets) and database — it must never live inside
   the git working tree, so a secret can't end up committed by accident:

   ```bash
   mkdir -p ~/ai-pc-instances/<character-name>
   ```

3. Copy the example env file into it and fill in your values:

   ```bash
   cp agents/pc/.env.example ~/ai-pc-instances/<character-name>/.env
   ```

   At minimum, set `ANTHROPIC_API_KEY`. Config and the database path are
   resolved relative to the current working directory, so all commands
   below are run from inside your instance directory.

## Creating a character

```bash
cd ~/ai-pc-instances/<character-name>
python /path/to/AI-PC/agents/pc/scripts/create_character.py
```

Add flags (`--class`, `--race`, `--alignment`, `--name`, ...) to constrain
any choice; anything you don't pass is left to the AI's judgment (see
REQUIREMENTS.md, Character Creation). This saves the character to the
SQLite database in your instance directory and prints the resulting
sheet, persona, and background.

## Chatting with the character (text-only, no Discord)

```bash
python /path/to/AI-PC/agents/pc/scripts/chat_repl.py "<character name>"
```

Type lines as the DM/table would speak them; type `quit` to exit. This
uses the same database as character creation, so it plays as the
character you just made.

## Running multiple characters/instances

Repeat setup with a separate instance directory (and, once Discord
support lands, a separate bot token) per character — see
REQUIREMENTS.md, Configuration & Secrets ("Multi-instance isolation").

## Contributing / running checks

For the dev workflow (lint, type-check, tests) and repo layout, see the
top-level [CONTRIBUTING.md](../../CONTRIBUTING.md).
