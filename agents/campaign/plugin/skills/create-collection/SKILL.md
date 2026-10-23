---
name: create-collection
description: Organize several independent D&D campaigns in one folder and git repository, each campaign in its own subfolder. Use when the DM wants a library or collection of campaigns, such as one per level range, or wants to organize their campaigns folder.
argument-hint: "[collection title]"
---

# Create a collection of campaigns

1. Work out the collection folder: the current working directory, unless
   the DM names another. Call the campaign MCP server's `campaign_status`
   on it.
   - If it is a campaign, stop: a collection is the folder that holds
     campaigns, usually the campaign's parent folder.
   - If it is already a collection or epic (`container` is set), say so
     and offer to create a campaign in a new subfolder instead.

2. Explain briefly: a collection holds independent campaigns, each in its
   own subfolder of the same git repository. Nothing ties the campaigns
   together; for one long story told across books, `/create-epic` is the
   better fit.

3. If `git.repository` is empty, the folder is not in a git repository.
   The DM normally creates it first; offer to create it now
   (`init_git=true`). If the DM declines, continue without git.

4. Ask for the collection's title, unless given: $ARGUMENTS. Then call
   `create_collection` with the absolute folder path, the title, and
   `init_git` if the DM agreed.

5. If `campaigns_found` is not empty, list them: they are already part of
   the collection.

6. Tell the DM how to add a campaign: create a subfolder, open it in VS
   Code, and run `/create-campaign`. Offer to create the subfolder and run
   `code <subfolder>` for them.
