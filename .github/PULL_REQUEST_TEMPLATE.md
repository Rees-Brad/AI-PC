## What changed and why

<!-- Summarize the change and the motivation. Link an issue if there is one. -->

## Agent(s)/area touched

- [ ] `shared/` (affects every agent - please call out what depends on it)
- [ ] `agents/pc/`
- [ ] CI / tooling / docs

## Testing

- [ ] Ran the relevant tests locally (`pytest`)
- [ ] Ran lint/type-check locally (`ruff check .`, `mypy ...` - see CONTRIBUTING.md)
- [ ] Added/updated tests for the behavior changed
- [ ] If this touches `agents/pc` behavior, manually exercised it (`scripts/create_character.py` / `scripts/chat_repl.py`) with a real `ANTHROPIC_API_KEY`
