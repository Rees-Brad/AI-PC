# Contributing to AI-PC

## Repo layout

This is a monorepo for a multi-agent AI tabletop system. Right now it holds:

```
shared/          # ai_pc_shared - infrastructure every agent reuses:
                 #   character/rules schema, persistence (SQLite via
                 #   SQLAlchemy), the bare Anthropic client wrapper.
agents/pc/       # ai_pc - the AI-backed Player Character agent (Discord
                 #   voice bot, character creation, gameplay tools).
```

More agents (DM, Notetaker, possibly NPC) are planned under `agents/` and
will follow the same shape: their own `pyproject.toml`, `src/`, `tests/`,
depending on `shared/` for anything genuinely cross-agent.

If you're adding something that only one agent needs, it belongs under
that agent's directory, not `shared/`. Only promote code to `shared/` once
a second agent actually needs it.

## Dev setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # or your preferred env tool
pip install -e ./shared -e './agents/pc[dev]'
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
mypy shared/src/ai_pc_shared agents/pc/src/ai_pc --ignore-missing-imports
pytest
python -c "import ai_pc_shared; import ai_pc"
```

## Pull requests

- Keep PRs small and focused on one agent/area where possible - use the PR
  template's checklist.
- CI (lint, type-check, tests, import check) must pass.
- Add or update tests for behavior you change. Pure logic (rules math,
  mapping functions) should be unit-testable without hitting the Anthropic
  API - see `agents/pc/tests/test_creation.py` for the pattern of testing
  the deterministic mapping logic separately from the live API call.
