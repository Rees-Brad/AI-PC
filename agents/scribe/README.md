# Scribe Agent

The campaign's memory: it listens to the table, keeps a running record of what
happened, and answers history questions. See [REQUIREMENTS.md](REQUIREMENTS.md)
for the full spec.

## Status

What works today: transcript ingestion, incremental summarization (recaps,
plot threads, NPC/location registry, awareness tracking), and the query
commands — all driven from the CLI scripts below.

Not implemented yet: the Discord bot and voice capture. Those depend on
Discord voice *receive*, which is community-library territory rather than an
officially supported part of the bot API, and is the main open risk in this
agent's design.

## Prerequisites

- Python 3.10+
- An Anthropic API key

## Setup

1. From the repo root, install the packages (`shared` first):

   ```bash
   pip install -e ./shared -e './agents/scribe[dev]'
   ```

2. Create an instance directory **outside this repo checkout** — it holds your
   `.env` and the campaign database:

   ```bash
   mkdir -p ~/ai-pc-instances/<campaign-name>
   cp agents/scribe/.env.example ~/ai-pc-instances/<campaign-name>/.env
   ```

   Set `ANTHROPIC_API_KEY` at minimum. All commands below run from inside that
   directory — config and the database path resolve relative to the working
   directory.

## Ingesting a session

Transcripts are one line per utterance, `Speaker: what they said`. Blank lines
and `#` comments are ignored.

```bash
cd ~/ai-pc-instances/<campaign-name>
python /path/to/AI-PC/agents/scribe/scripts/ingest_transcript.py session-01 transcript.txt
```

This buffers the lines, summarizes them, and merges the result into the
campaign record. Run it repeatedly during a session — each run updates the
recap in place rather than starting over.

Pass `--finalize` when the session ends. That marks the session complete and
**discards its transcript buffer**: the durable record is the summarized
material, not an archive of everything said.

## Querying the record

```bash
python /path/to/AI-PC/agents/scribe/scripts/query.py recap
python /path/to/AI-PC/agents/scribe/scripts/query.py who "Ser Aldric"
python /path/to/AI-PC/agents/scribe/scripts/query.py where "Blackmoor"
python /path/to/AI-PC/agents/scribe/scripts/query.py threads
python /path/to/AI-PC/agents/scribe/scripts/query.py knows "the ledger"
```

`knows` reports which characters are aware of an event and whether they learned
it firsthand or secondhand. Awareness is inferred during ingestion, while the
transcript still exists — it cannot be recovered afterwards.

## The campaign database

The Scribe is the campaign database's only writer. Other agents open it
read-only via `ai_pc_shared.campaign.db.open_campaign_readonly`, which SQLite
enforces at the connection level — a consumer that tries to write gets an
error rather than corrupting the record.

A PC agent reads this same file; point its `AI_PC_CAMPAIGN_DB_PATH` at it.

DM-private notes live in the same database but are deliberately absent from the
shared read-only surface, so they never reach other agents.

## Contributing / running checks

See the top-level [CONTRIBUTING.md](../../CONTRIBUTING.md).
