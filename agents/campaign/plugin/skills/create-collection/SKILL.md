---
name: create-collection
description: Organize several D&D campaigns in one folder that is a git repository, with each campaign as a submodule. Use when the DM wants a library or collection of campaigns, wants to organize their campaigns folder, or wants campaigns versioned together.
argument-hint: "[collection title]"
---

# Create a collection of campaigns

1. Work out the collection folder: the current working directory, unless
   the DM names another. Call the campaign MCP server's `campaign_status`
   on it.
   - If it is a campaign, stop: a collection is the folder that holds
     campaigns, usually the campaign's parent folder.
   - If `is_collection` is already true, say so and offer to add campaigns
     to it instead (step 4).

2. Explain briefly what a collection is: the folder becomes a git
   repository, and each campaign inside it stays its own repository,
   registered as a submodule. New campaigns created inside it and running
   copies started from them are added automatically. Everything stays on
   this computer.

3. Ask for the collection's title, unless given: $ARGUMENTS. Then call
   `create_collection` with the absolute folder path and the title.

4. If `campaigns_found` is not empty, list them and ask which to add. For
   each one the DM picks, call `add_to_collection` with its absolute path.
   A campaign that is not yet a git repository is made one; a campaign with
   unsaved changes must be saved first with `/save-campaign` from its
   folder.

5. Tell the DM how to continue: open a new folder inside the collection and
   run `/create-campaign` to add a campaign. Mention that running git
   commands by hand on a collection needs
   `-c protocol.file.allow=always` for submodule operations such as
   `git clone --recurse-submodules`, because git blocks local submodule
   copies by default.
