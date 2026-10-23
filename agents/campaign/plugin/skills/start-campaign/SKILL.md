---
name: start-campaign
description: Make a running copy of a finished master D&D campaign for a group of players, so games are run from the copy and the master stays as authored. Use when the DM is ready to start playing a campaign with a group.
argument-hint: "[group name]"
---

# Start a running copy for a group

1. Call the campaign MCP server's `campaign_status` tool with the absolute
   path of the current working directory.
   - If it is a running copy, stop. Explain that running copies are made
     from the master, and give the master's path from `source_master`.
   - If it is not a campaign, stop and suggest `/create-campaign`.

2. Run `check_campaign`. If it reports errors, list them and ask whether the
   DM wants to fix them first or start anyway.

3. Ask for the group's name, unless one was given: $ARGUMENTS

4. If the master is a git repository with uncommitted changes, show them
   and offer to save them first with `/save-campaign`. The running copy is
   cloned from the last commit, so uncommitted work would be left out.

5. Tell the DM where the copy will be created. The default is next to the
   master, named `<master>--<group>`. Ask whether that is fine or whether
   they want another location. If the master is in a collection or epic
   (`belongs_to` is set), the copy is a sibling folder in the same
   repository and is committed there. For an epic, say that running a
   whole epic across books is still being designed; this starts one book.

6. Call `start_campaign` with the master folder, the group name, and the
   destination if the DM chose one.

7. Explain what happened and what comes next:
   - The **running copy** at the new path is where this group's games will
     be run. Game sessions and updates after each session change its files.
   - The **master** is unchanged and can start more groups later.
   - Ask the DM to open the running copy in VS Code (File > Open Folder),
     and offer to run `code <folder>` for them.
   - Game Session and Update modes, which work with the Scribe, are not
     available in this version yet.
