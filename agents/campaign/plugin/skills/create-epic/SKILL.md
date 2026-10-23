---
name: create-epic
description: Start or resume an epic - one long D&D story told as a series of books, each book a full campaign in its own subfolder, tied together by an epic overview and epic-wide indexes. Use when the DM wants a multi-book saga or series, or wants to work on an existing epic as a whole.
argument-hint: "[epic title]"
---

# Create or resume an epic

Follow the `campaign-rules` skill throughout, especially "Books of an epic".

1. Call the campaign MCP server's `campaign_status` with the absolute path
   of the current working directory.

2. **If it is an epic** (`container.kind` is `epic`), resume it:
   - Read `epic.md`, the epic's three indexes, `WORKLOG.md` (latest
     entries), and `OPEN_ITEMS.md`. Skim each book's `campaign.md`.
   - Run `check_epic` and summarize its findings briefly.
   - Summarize where the epic stands: the story, the books in order with
     their level ranges and progress, open items (the DM's priorities
     first), and problems found. Suggest what to work on next.

3. **If it is a campaign, a running copy, or a collection**, stop and
   explain: an epic is the folder that holds the books. Offer to set one up
   in another folder.

4. **Otherwise, create the epic:**
   - Explain briefly: an epic is one story told across books. Each book is
     a full campaign in its own subfolder; `epic.md` holds the overall
     story and the books in reading order; the epic's indexes track NPCs,
     items, and places that matter across books.
   - Ask for the title, unless given: $ARGUMENTS. Tell the DM the epic uses
     D&D 5e (2024) unless they want another edition; every book will use
     the same edition.
   - If `git.repository` is empty, offer to create the git repository
     (`init_git=true`), as the DM normally creates it first.
   - Call `create_epic`, then point the DM to `GETTING_STARTED.md` (Ctrl+Shift+V
     to read it formatted).

5. Develop the epic with the DM: the overarching story and its ending, the
   number of books, what each book covers, and the level range of each.
   Write the story into `epic.md` and the planned books into its Books list
   as they are decided, and keep `OPEN_ITEMS.md` current.

6. To start a book, create its subfolder (such as `01-the-eye-of-the-world`),
   ask the DM to open it in VS Code, and run `/create-campaign` there.
   Offer to run `code <subfolder>` for them.
