# Contributing to AI-PC

## Repo layout

This is a monorepo for a multi-agent AI tabletop system. Right now it holds:

```
shared/          # ai_pc_shared - infrastructure every agent reuses:
                 #   character/rules schema, persistence (SQLite via
                 #   SQLAlchemy), the campaign record, the Anthropic client.
agents/campaign/ # ai_campaign - the Campaign Agent: a Claude Code plugin and
                 #   MCP server for creating and running campaigns.
agents/scribe/   # ai_scribe - the Scribe: transcript summarization, the
                 #   campaign record, session summaries, and DM queries.
agents/pc/       # ai_pc - the AI Player Character agent (on hold).
```

The DM and NPC agents are on hold. New agents follow the same shape: their
own `pyproject.toml`, `src/`, `tests/`, depending on `shared/` for anything
genuinely cross-agent.

If you're adding something that only one agent needs, it belongs under
that agent's directory, not `shared/`. Only promote code to `shared/` once
a second agent actually needs it.

## Dev setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # or your preferred env tool
pip install -e ./shared -e './agents/pc[dev]' -e './agents/campaign[dev]' -e './agents/scribe[dev]'
```

Install order matters: `shared` must be installed before `agents/pc`,
since `agents/pc` depends on it as a local editable package (it isn't
published anywhere).

To test `agents/pc` live (character creation, chat), copy
`agents/pc/.env.example` to `agents/pc/.env` and set `ANTHROPIC_API_KEY`.

## Running checks locally

These are exactly what CI runs (`.github/workflows/ci.yml`):

```bash
ruff check .
mypy shared/src/ai_pc_shared agents/pc/src/ai_pc agents/campaign/src/ai_campaign agents/scribe/src/ai_scribe --ignore-missing-imports
pytest
python -c "import ai_pc_shared; import ai_pc; import ai_campaign.mcp_server; import ai_scribe.mcp_server"
```

## Pull requests

- Keep PRs small and focused on one agent/area where possible - use the PR
  template's checklist.
- CI (lint, type-check, tests, import check) must pass.
- Add or update tests for behavior you change. Pure logic (rules math,
  mapping functions) should be unit-testable without hitting the Anthropic
  API - see `agents/pc/tests/test_creation.py` for the pattern of testing
  the deterministic mapping logic separately from the live API call.
