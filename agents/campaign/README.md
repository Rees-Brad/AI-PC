# Campaign Agent

The Campaign Agent helps a DM write D&D campaigns as Markdown files in VS
Code, with Claude Code as the conversation. It is a Claude Code plugin with a
Python MCP server for the campaign tools.

| Document | For | What it covers |
|---|---|---|
| [User Guide](USER_GUIDE.md) | DMs and authors | How to work with the agent: structures, creating, checking, running, publishing |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Planning | What the agent must do, including what is not built yet |
| [DESIGN.md](DESIGN.md) | Developers | How it is built: tools, files, git, publishing |
| [TESTING.md](TESTING.md) | Beta testers | Scenarios to try and how to report problems |

## Status

| Available now | Coming |
|---|---|
| Creating and checking campaigns; collections and epics; maps; encounter summaries and trackers for D&D 5e (2024 and 2014) and D&D 3.5; saving and resuming; running copies | Game Session and Update modes with the Scribe; splitting a book of an epic |
| Release 2 beta: `/publish-campaign` makes a digital PDF | Release 2: importing a published PDF, watermarks, the print-ready PDF; later, styling themes |

## Requirements

- VS Code with the Claude Code extension, signed in with your own Claude
  account. The Claude Code CLI works too.
- Python 3.10 or later.
- git, recommended. Campaigns work without it, but running copies are then
  plain folder copies with no history.
- A clone of this repository.
- For `/publish-campaign`, the Pango text library, which WeasyPrint uses to
  make PDFs. Ubuntu and Debian: `sudo apt install libpango-1.0-0
  libpangoft2-1.0-0`. macOS: `brew install pango`. See WeasyPrint's
  installation guide for Windows.

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
directly from it. After `git pull`, reinstall the package if its
dependencies changed (step 1), then start a new session to pick up changes.

To get started, open an empty folder in VS Code and run `/create-campaign`;
the [User Guide](USER_GUIDE.md) explains the rest.

## Troubleshooting

| Problem | What to do |
|---|---|
| The commands don't appear | Reload VS Code. Check `claude plugin list` shows `campaign-agent@ai-pc` as enabled. |
| `campaign` server not connected | Run `claude mcp list`. Check the Python interpreter option points at the Python where you installed the package: `claude plugin configure campaign-agent@ai-pc`. |
| `No module named ai_campaign` | The configured Python does not have the package. Repeat step 1 with that Python. |
| Publishing fails with a Pango or `libgobject` error | Install Pango (see Requirements), then start a new session so the MCP server restarts. |
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
`claude --plugin-dir agents/campaign/plugin`. The modules and file formats
are described in [DESIGN.md](DESIGN.md).
