# AI-PC

An AI-backed tabletop RPG toolkit: autonomous AI agents that sit in at a
D&D (or other TTRPG) table.

This is a monorepo. Today it holds:

- **[`agents/pc/`](agents/pc/)** - the AI Player Character agent. Owns its
  own character sheet, rolls its own dice, applies D&D 5e rules, and plays
  as a full autonomous player over Discord voice/text. See
  [`agents/pc/REQUIREMENTS.md`](agents/pc/REQUIREMENTS.md) for its
  interfaces and behavior spec.
- **[`shared/`](shared/)** - infrastructure reused across agents:
  character/rules schema, persistence, the Anthropic client wrapper.

Planned, not yet built: `agents/dm/` (Dungeon Master agent),
`agents/notetaker/` (session notes/summaries), and possibly `agents/npc/`
(non-player characters). They'll follow the same shape as `agents/pc/`,
built on the same `shared/` infrastructure.

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and how to run
tests/lint/type-checks locally.

## License

Proprietary - see [LICENSE](LICENSE). All rights reserved; this may
change to an open-source license in the future.
