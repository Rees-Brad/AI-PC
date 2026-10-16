# Campaign Agent

The Campaign Agent provides a local browser-based conversation for reviewing,
creating, and updating D&D campaigns stored as Markdown files.

## Run locally

From the repository root, install the shared library and agent in editable mode:

```bash
pip install -e ./shared -e ./agents/campaign
```

The Campaign Agent uses `~/ai-pc-campaigns` as its instance and campaign
directory. It reads configuration from the top-level
`~/ai-pc-campaigns/.env`, independently of the directory from which the
server is launched. Create it from the example:

```bash
mkdir -p ~/ai-pc-campaigns
cp agents/campaign/.env.example ~/ai-pc-campaigns/.env
```

Edit `~/ai-pc-campaigns/.env` and set `ANTHROPIC_API_KEY`, then start the
server with `ai-campaign`. If the key is already in another agent's `.env`
on this same machine, you can instead set `AI_CAMPAIGN_ENV_FILE` to that
file's path. The Campaign Agent reads but does not modify it. `.env` files
are ignored by Git; keep secrets out of committed files and chat messages.

Open <http://127.0.0.1:8765>. Set `AI_CAMPAIGN_ROOT` to change the directory
where campaigns are listed and approved Markdown proposals are written. The
default is `~/ai-pc-campaigns`, with campaign folders stored beneath it.
`AI_CAMPAIGN_HOST`, `AI_CAMPAIGN_PORT`, and `AI_CAMPAIGN_MODEL` can also be
set through the environment or `.env` file. `AI_CAMPAIGN_MAX_CONTEXT_KB`
sets the maximum size of uploaded review documents, supplied session records,
and campaign context sent with a chat request; it defaults to 500 KB.

Reviewer Mode accepts text documents and PDFs with selectable text. Scanned
PDFs without an OCR text layer are not supported. In Create Mode, attach
optional text or selectable-text PDF starting material, or choose an existing
campaign to continue from its saved Markdown. The Campaign directory field
sets the absolute folder where campaign subfolders are listed and created;
the browser remembers the selected path. Update Mode currently accepts a
Scribe recap pasted by the user; a direct Scribe integration is not
implemented. In Creation and Update modes, generated Markdown is only written
after the user reviews the proposal and selects **Apply files**.