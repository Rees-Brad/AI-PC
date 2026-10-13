# Campaign Agent

The Campaign Agent provides a local browser-based conversation for reviewing,
creating, and updating D&D campaigns stored as Markdown files.

## Run locally

From the repository root, install the shared library and agent in editable mode:

```bash
pip install -e ./shared -e ./agents/campaign
```

Set an Anthropic API key and start the local server:

```bash
export ANTHROPIC_API_KEY="..."
ai-campaign
```

Open <http://127.0.0.1:8765>. Set `AI_CAMPAIGN_ROOT` to change the directory
where campaigns are listed and approved Markdown proposals are written. The
default is `~/ai-pc-campaigns`. `AI_CAMPAIGN_HOST`, `AI_CAMPAIGN_PORT`, and
`AI_CAMPAIGN_MODEL` can also be set through the environment.

Reviewer Mode accepts a Markdown file from the browser and does not write
campaign files. Update Mode currently accepts a Scribe recap pasted by the
user; a direct Scribe integration is not implemented. In Creation and Update
modes, generated Markdown is only written after the user reviews the proposal
and selects **Apply files**.