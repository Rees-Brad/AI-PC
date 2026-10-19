# Campaign Agent

The Campaign Agent helps a DM create D&D campaigns as Markdown files in VS
Code, with Claude Code as the conversation. It is a Claude Code plugin with a
Python MCP server for the campaign tools. See
[REQUIREMENTS.md](REQUIREMENTS.md) for the full design and
[TESTING.md](TESTING.md) for what to try.

This version supports:

| Command | What it does |
|---|---|
| `/create-campaign` | Starts a new master campaign in an empty folder, or resumes one. |
| `/check-campaign` | Reports broken links, unlinked maps, index entries that point nowhere, sections missing from their outlines, and numbering problems, without changing anything. |
| `/start-campaign` | Makes a running copy of a master campaign for a group. |

Claude Code may show the commands with the plugin name as a prefix, such as
`/campaign-agent:create-campaign`. Game Session and Update modes, which work
with the Scribe, come in a later version.

## Requirements

- VS Code with the Claude Code extension, signed in with your own Claude
  account. The Claude Code CLI works too.
- Python 3.10 or later.
- git, recommended. Campaigns work without it, but running copies are then
  plain folder copies with no history.
- A clone of this repository.

## Install

Run these from the root of your clone of this repository.

1. **Install the MCP server package.** A virtual environment is
   recommended, so the package and its `mcp` dependency don't clash with
   other Python tools:

   ```bash
   python3 -m venv ~/.venvs/ai-campaign
   ~/.venvs/ai-campaign/bin/pip install -e ./agents/campaign
   ```

   On Ubuntu, `python3 -m venv` needs the `python3-venv` package. To skip
   the virtual environment, run `python3 -m pip install --user -e ./agents/campaign`
   instead and use `python3` as the interpreter in step 2.

2. **Install the plugin.** The VS Code extension has no `/plugin` command,
   but it shares plugin settings with the `claude` CLI, so install from a
   terminal:

   ```bash
   claude plugin marketplace add "$PWD"
   claude plugin install campaign-agent@ai-pc
   echo "{\"python\": \"$HOME/.venvs/ai-campaign/bin/python\"}" \
     | claude plugin configure campaign-agent@ai-pc --values-stdin
   ```

   The last command sets the plugin's **Python interpreter** option to the
   Python from step 1.

   If `claude` is not on your PATH, use the copy bundled with the VS Code
   extension:
   - Remote or WSL: `~/.vscode-server/extensions/anthropic.claude-code-<version>/resources/native-binary/claude`
   - Desktop: `~/.vscode/extensions/anthropic.claude-code-<version>/resources/native-binary/claude`

3. **Check the server.** `claude mcp list` should show
   `plugin:campaign-agent:campaign` as connected.

4. **Reload VS Code** (or start a new Claude Code session) so it loads the
   plugin.

Because the marketplace is your local clone, Claude Code reads the plugin
directly from it. After `git pull`, start a new session to pick up changes.

## Use

1. Open an empty folder in VS Code and run `/create-campaign`. The agent
   sets up `campaign.md`, the NPC, item, and location indexes, and the
   `maps/` and `chapters/` folders, then develops the campaign with you. It
   recommends making the campaign a git repository.
2. Keep the Explorer, the Markdown preview, and a map open beside the
   conversation. Save maps as PNG, JPEG, or WebP into `maps/`.
3. Run `/check-campaign` at any time. A new campaign reports that it has no
   goal and no adventure yet; that is expected.
4. When the campaign is ready to play, run `/start-campaign` from the
   master.

### Master campaigns and running copies

The folder you create is the **master**: the campaign as written. Games
aren't run from it, because game sessions and the updates after them change
the files. `/start-campaign` makes a **running copy** for one group, next to
the master as `<master>--<group>`, and you open that folder to run the
group's games. One master can start any number of groups.

A `.campaign/campaign.json` marker records which kind of folder it is. Don't
edit it by hand.

`/start-campaign` refuses when:
- the folder is already a running copy;
- the master is a git repository with uncommitted changes, because the copy
  is cloned from the last commit; or
- the destination folder already exists.

## Troubleshooting

| Problem | What to do |
|---|---|
| The commands don't appear | Reload VS Code. Check `claude plugin list` shows `campaign-agent@ai-pc` as enabled. |
| `campaign` server not connected | Run `claude mcp list`. Check the Python interpreter option points at the Python where you installed the package: `claude plugin configure campaign-agent@ai-pc`. |
| `No module named ai_campaign` | The configured Python does not have the package. Repeat step 1 with that Python. |
| Committing fails inside a campaign | Set your git identity: `git config --global user.name` and `user.email`. |

To uninstall:

```bash
claude plugin uninstall campaign-agent@ai-pc
claude plugin marketplace remove ai-pc
```

## Develop

Run the checks from the repository root:

```bash
python3 -m pytest agents/campaign
ruff check .
claude plugin validate --strict agents/campaign/plugin
```

Python changes take effect when the MCP server restarts, for example in a
new session. To load the plugin without installing it, start the CLI with
`claude --plugin-dir agents/campaign/plugin`.

| Path | Contents |
|---|---|
| `plugin/.claude-plugin/plugin.json` | Plugin manifest and the Python interpreter option |
| `plugin/.mcp.json` | Starts the MCP server |
| `plugin/skills/campaign-rules/` | Rules the agent follows in any campaign folder |
| `plugin/skills/create-campaign/`, `check-campaign/`, `start-campaign/` | The commands |
| `src/ai_campaign/mcp_server.py` | MCP tools |
| `src/ai_campaign/structure.py` | Reading and checking campaign folders |
| `src/ai_campaign/lifecycle.py` | Creating masters and starting running copies |
| `src/ai_campaign/marker.py` | The `.campaign/campaign.json` marker |
| `src/ai_campaign/pdf.py` | Text extraction from PDF starting material |
