# Scribe Agent

The campaign's memory: it listens to the table, keeps a running record of what
happened, and answers history questions. It runs on the DM's computer. See
[REQUIREMENTS.md](REQUIREMENTS.md) for the full design.

## Status

Works today, driven from the CLI scripts below:

- Transcript ingestion and incremental summarization into the campaign
  record: recaps, plot threads, the NPC, location, and faction registry, and
  who knows what.
- Keeping the record inside a Campaign Agent running copy, and writing a
  short summary of each finalized session to its `sessions/` folder.
- Private DM queries from Claude Code through the `scribe` plugin, including
  the DM's private notes.

Not implemented yet: the Discord bot and voice capture, and the DM-only
`/note` and `/correct` commands. Discord voice *receive* is community-library
territory rather than an officially supported part of the bot API, and is the
main open risk in this agent's design. It will be built with the Campaign
Agent's Game Session Mode.

## Setup

You need Python 3.10 or later and an Anthropic API key.

1. From the repository root, install the packages (`shared` first). A
   virtual environment works too; see the Campaign Agent's README.

   ```bash
   python3 -m pip install --user -e ./shared -e './agents/scribe[dev]'
   ```

2. Create an instance directory **outside this repository and outside any
   campaign folder** for the Scribe's `.env`:

   ```bash
   mkdir -p ~/ai-pc-instances/scribe
   cp agents/scribe/.env.example ~/ai-pc-instances/scribe/.env
   ```

   Set `ANTHROPIC_API_KEY`. The Scribe reads `.env` from the working
   directory, or from the file named by `SCRIBE_ENV_FILE`.

## Where the record lives

- **With the Campaign Agent:** pass `--campaign-folder <running copy>` (or
  set `SCRIBE_CAMPAIGN_FOLDER`). The database is kept in the running copy's
  `.scribe/campaign.db`, which the campaign's `.gitignore` keeps out of
  git. The Scribe refuses a master campaign: games are recorded in running
  copies made with `/start-campaign`.
- **On its own:** the database is `CAMPAIGN_DB_PATH`, `./campaign.db` by
  default.

## Ingesting a session

Transcripts are one line per utterance, `Speaker: what they said`. Blank lines
and `#` comments are ignored.

```bash
cd ~/ai-pc-instances/scribe
python /path/to/AI-PC/agents/scribe/scripts/ingest_transcript.py \
  session-01 transcript.txt --campaign-folder ~/Campaigns/crown--tuesday
```

This buffers the lines, summarizes them, and merges the result into the
campaign record. Run it repeatedly during a session; each run updates the
recap in place rather than starting over.

Pass `--finalize` when the session ends. That marks the session complete,
**discards its transcript buffer** (the durable record is the summarized
material, not an archive of everything said), and, with a campaign folder,
writes the session summary to `sessions/<YYYY-MM-DD>.md`. A second session
on the same date gets a `-2` suffix. The Scribe owns these files: when the
record is corrected, it rewrites the summary.

## Querying the record

From a terminal:

```bash
python /path/to/AI-PC/agents/scribe/scripts/query.py recap
python /path/to/AI-PC/agents/scribe/scripts/query.py who "Ser Aldric"
python /path/to/AI-PC/agents/scribe/scripts/query.py where "Blackmoor"
python /path/to/AI-PC/agents/scribe/scripts/query.py threads
python /path/to/AI-PC/agents/scribe/scripts/query.py knows "the ledger"
python /path/to/AI-PC/agents/scribe/scripts/query.py sessions
python /path/to/AI-PC/agents/scribe/scripts/query.py notes
python /path/to/AI-PC/agents/scribe/scripts/query.py search "ledger"
```

Add `--campaign-folder <running copy>` before the command to read a running
copy's record. `knows` reports which characters are aware of an event and
whether they learned it firsthand or secondhand; awareness is inferred during
ingestion, while the transcript still exists. `notes` and `search` include
the DM's private notes.

### Private questions from Claude Code

The `scribe` plugin lets the DM ask the Scribe questions in plain language
from VS Code, at any time, including during a session. Answers go only to
the DM and can include DM-private notes. Install it like the Campaign Agent
plugin:

```bash
claude plugin marketplace add /path/to/AI-PC   # once, if not already added
claude plugin install scribe@ai-pc
echo '{"python": "python3"}' | claude plugin configure scribe@ai-pc --values-stdin
```

Use the Python where you installed the package. In a running copy, ask
something like "What did the party promise the harbormaster?", or run
`/ask-scribe <question>`.

## The campaign database

The Scribe is the campaign database's only writer. Readers open it read-only
via `ai_pc_shared.campaign.db.open_campaign_readonly`, which SQLite enforces
at the connection level: a reader that tries to write gets an error rather
than corrupting the record. The `scribe` plugin's query tools read it this
way.

DM-private notes live in the same database. They are available to private
DM queries, and deliberately absent from the shared read-only repository
used by other agents.

## Contributing / running checks

See the top-level [CONTRIBUTING.md](../../CONTRIBUTING.md).
