---
name: save-campaign
description: Save progress on a D&D campaign so work can resume later. Updates the work log and open items, checks the campaign, and takes a snapshot. Use when the DM wants to save, snapshot, checkpoint, or stop for now, or at the end of a working session.
argument-hint: "[what was worked on]"
---

# Save the campaign

Follow the `campaign-rules` skill throughout.

1. Call the campaign MCP server's `campaign_status` tool with the absolute
   path of the current working directory. It can be a campaign, a
   collection, or an epic; if it is none of these, stop and suggest
   `/create-campaign`. If `missing_agent_files` is not empty, call
   `ensure_campaign_docs` first.

2. Update `OPEN_ITEMS.md` from this conversation:
   - check off items that were resolved, with today's date;
   - add new open questions, placeholders, and things to come back to;
   - keep the DM's order, priorities, and own items.

3. Add an entry at the top of `WORKLOG.md`, under the title and intro, for
   today: what was done, decisions made and why, and ideas set aside. Use
   $ARGUMENTS as a hint if given. Keep it to a few bullet points.

4. Run `check_campaign`. If it reports errors, list them and ask whether to
   fix them now or save as is; note any left unfixed in `OPEN_ITEMS.md`.

5. Call `snapshot_campaign` with a summary of a few words, such as
   "Chapter 2 encounters drafted". In a git repository it commits only
   this folder, so other campaigns or books in the same repository are
   left alone; saving an epic's own folder commits the whole epic.

6. Tell the DM in two or three lines what was saved, how many open items
   remain (and the top priority), and that `/create-campaign` will pick up
   from here next time.
