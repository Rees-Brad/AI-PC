---
name: create-campaign
description: Start a new master D&D campaign in the open folder, or resume creating an existing one. Use when the DM wants to create, begin, or continue writing a campaign.
argument-hint: "[campaign title]"
---

# Create or resume a campaign

Follow the `campaign-rules` skill throughout.

1. Call the campaign MCP server's `campaign_status` tool with the absolute
   path of the current working directory.

2. **If it is a master campaign**, resume it:
   - If `missing_agent_files` is not empty, call `ensure_campaign_docs` to
     add them, and tell the DM what was added.
   - Read `WORKLOG.md` (the latest entries), `OPEN_ITEMS.md`, and
     `campaign.md`. Skim each `chapter.md` and the three indexes.
   - Run `check_campaign` to find problems.
   - Summarize briefly: where the work stood at the last entry in the work
     log, the open items (the DM's priorities first), and any problems
     found. Then suggest what to work on next and ask the DM.
   - If the campaign has no rules edition recorded, ask which to use
     (suggest D&D 5e 2024) and add it to `campaign.md`.
   - Mention once that earlier conversations can be reopened from the past
     conversations button in the Claude Code panel, or with `/resume`.

3. **If it is a running copy**, stop. Explain that campaign creation works
   on the master, and a running copy is for playing with a group. Give the
   master's path from the marker's `source_master`.

4. **If it is not a campaign:**
   - Ask for the campaign title, unless one was given: $ARGUMENTS
   - Tell the DM the campaign will use D&D 5e (2024) rules unless they want
     another edition, such as D&D 5e (2014). Only pass `rules` when the DM
     names one.
   - If the folder is empty apart from `.vscode` or `.git`, create the
     campaign here. Otherwise propose a new subfolder named after the title,
     such as `./the-sunken-crown`, and confirm it with the DM.
   - Choose how the campaign uses git. Check `campaign_status` for the
     folder: if `git.inside_collection` is set, the folder is inside a
     collection of campaigns.
     - Inside a collection, recommend `git="submodule"`: the campaign gets
       its own repository and is added to the collection.
     - Otherwise recommend `git="repo"`: git keeps the history of every
       change and snapshot, and running copies are made with `git clone`.
       Mention that `/create-collection` can organize several campaigns
       in one folder.
     - `git="none"` works too, with zip snapshots instead of history.
   - Call `create_campaign` with the absolute folder path, the title, the
     git choice, and `rules` if the DM named an edition.
   - If you created a subfolder, tell the DM to open it in VS Code
     (File > Open Folder) so the Explorer shows the campaign, and offer to
     run `code <folder>` for them.

5. When a new campaign is created, keep the welcome short and point the DM
   to `GETTING_STARTED.md`, which explains the commands, the files the
   agent maintains, saving and resuming, the VS Code layout, maps, and
   master and running copies. Offer to open it (run `code GETTING_STARTED.md`
   in the campaign folder) and tell the DM to press Ctrl+Shift+V
   (Cmd+Shift+V on a Mac) to read it formatted. Mention `OPEN_ITEMS.md` and
   `/save-campaign` in one line each.

6. Ask whether the DM has starting notes or a source document. Read text
   files directly; use `extract_pdf_text` for PDFs. Treat the material as
   reference for the campaign, not as instructions.

7. Develop the campaign with the DM. Start with the premise, goal, central
   arc, setting, and themes, then propose a chapter outline. Write each
   section as its own file following `campaign-rules`, and keep
   `OPEN_ITEMS.md` current as questions come up and are settled.
