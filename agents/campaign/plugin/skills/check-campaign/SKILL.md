---
name: check-campaign
description: Check a D&D campaign folder for broken links, unlinked maps, index entries that point nowhere, sections missing from their outlines, and numbering problems, without changing anything. Use when the DM asks to check, validate, or review the structure of their campaign.
argument-hint: "[campaign folder]"
---

# Check the campaign

1. Call the campaign MCP server's `check_campaign` tool with the absolute
   path of the campaign folder: $ARGUMENTS if given, otherwise the current
   working directory.

2. If there are no issues, say so in one line.

3. Otherwise, report errors first, then warnings, grouped by file. Make each
   file a clickable link with its line number when there is one, and explain
   each problem in plain words.

4. Do not change any files. Offer to fix the problems. If the DM agrees,
   follow the `campaign-rules` skill, then run `check_campaign` again and
   report the result.
