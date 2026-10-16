# AI-PC

An AI-backed tabletop RPG toolkit: autonomous AI agents that sit in at a
D&D (or other TTRPG) table.

This is a monorepo.

## First release

The first release is two agents that run on the DM's computer:

- **[`agents/campaign/`](agents/campaign/)** - the Campaign Agent. Helps the
  DM create a campaign in VS Code with Claude Code, run game sessions from
  a copy of it, and update the rest of the campaign after each session.
  See [`agents/campaign/REQUIREMENTS.md`](agents/campaign/REQUIREMENTS.md).
- **[`agents/scribe/`](agents/scribe/)** - the Scribe. Listens to the
  table in Discord, keeps the campaign's record of what happened, answers
  players' questions in Discord and the DM's privately, and saves a short
  summary of each session in the campaign folder. See
  [`agents/scribe/REQUIREMENTS.md`](agents/scribe/REQUIREMENTS.md).

[`shared/`](shared/) holds infrastructure reused across agents:
character/rules schema, persistence, and the Anthropic client wrapper.

## On hold

The AI Player Character agent ([`agents/pc/`](agents/pc/)), the Dungeon
Master agent ([`agents/dm/`](agents/dm/)), and the NPC agent
([`agents/npc/`](agents/npc/)) are on hold. Their requirements will be
redone after the first release.

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and how to run
tests/lint/type-checks locally.

## License

Proprietary - see [LICENSE](LICENSE). All rights reserved; this may
change to an open-source license in the future.
