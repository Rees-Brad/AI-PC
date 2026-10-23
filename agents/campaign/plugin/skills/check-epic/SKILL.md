---
name: check-epic
description: Check the books of a D&D epic against each other - the book list, rules editions, links, NPCs who die or items destroyed in one book but reappear later, recurring entries missing from the epic index - and then review the story across books for timeline, character, and foreshadowing problems. Changes nothing. Use when the DM asks to check, review, or validate an epic or its consistency.
argument-hint: "[epic folder]"
---

# Check an epic

1. Use the epic folder: $ARGUMENTS if given, otherwise the current working
   directory, or the epic it belongs to (`belongs_to` in
   `campaign_status`) if the current folder is a book.

2. Call the campaign MCP server's `check_epic` with its absolute path.
   Report errors first, then warnings, grouped by book, with clickable file
   links and line numbers. Keep each book's own campaign issues brief; the
   cross-book findings matter most here.

3. Then review the story across the books yourself. Read `epic.md`, the
   epic's indexes, and each book's `campaign.md` and chapter outlines in
   reading order, opening sections where needed. Look for:
   - **Timeline:** events out of order, travel or time that does not add
     up, a book depending on something that happens only in a later book.
   - **Characters:** an NPC whose motives, allegiance, or knowledge change
     between books without a reason in the story; someone who knows
     something before they could have learned it.
   - **Foreshadowing and threads:** set-ups never paid off, payoffs with no
     set-up, threads dropped between books.
   - **Progression:** level ranges with gaps or overlaps between books, and
     encounters out of line with a book's level range.

4. Present the story findings separately from the tool's findings, each
   with the books and files involved and a suggested fix. They are the
   agent's reading, not certainties; say how confident you are.

5. Do not change any files. Offer to fix what the DM chooses, then run
   `check_epic` again.
