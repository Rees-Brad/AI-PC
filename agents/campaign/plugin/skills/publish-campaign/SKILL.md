---
name: publish-campaign
description: Publish a finished master D&D campaign as a PDF for readers or buyers, with a title page, copyright page, contents, bookmarks, clickable links, maps, and printable encounter trackers. An epic is published as one PDF per book. Use when the author or DM wants to publish, export, print, or make a PDF of a campaign or epic, or to set its author, copyright, or edition.
argument-hint: "[Letter|A4] [folder]"
---

# Publish the campaign

This is a Release 2 beta. It makes the digital PDF only; the print-ready
PDF, watermarks, and embedding the source for import come later.

1. Call the campaign MCP server's `campaign_status` tool with the absolute
   path of the folder: the folder in $ARGUMENTS if given, otherwise the
   current working directory.
   - A **running copy** is never published, because it holds play history.
     Say so and offer to publish its master (`source_master` in the
     marker) instead.
   - An **epic** is published as one PDF per book, in the order of the
     Books list in `epic.md`. Publishing details set on the epic apply to
     every book unless a book sets its own.
   - A **collection** is not published as a whole. Ask which campaign to
     publish.
   - Anything else is not a campaign; say so and stop.

2. Call `publish_readiness`. Report errors first, then warnings, grouped by
   file, with each file as a clickable link and its line number. Explain
   that warnings such as an adventure with no map may be fine. Ask whether
   to fix problems first or publish anyway; the author decides. If they
   want fixes, follow the `campaign-rules` skill, then run the check again.

3. If the author, copyright holder, or edition is missing, ask for them,
   along with anything else the author wants: rights statement (default
   "All rights reserved."), license or attribution text, credits, a cover
   image in the folder, a copyright line in every page's footer, page size
   (Letter or A4), and an appendix with full-page copies of every map.
   - Suggest the license text include the SRD attribution that
     `campaign.md` records for the rules edition, since the campaign uses
     SRD material.
   - Save them with `set_publish_details`. They are kept for later
     editions, so on later publishes only confirm the edition: ask whether
     this is a new edition and, if so, its number.

4. Remind the author once, briefly: they are responsible for having the
   rights to everything they publish, including maps and artwork, and
   material from a system reference document needs its attribution or
   license. Do not judge whether they may sell it.

5. Call `publish_campaign`. Page size from $ARGUMENTS overrides the saved
   one for this publish.

6. Report each PDF as a clickable link with its page count, edition, and
   page size, and the counts of sections, maps, and encounter trackers.
   Ask the author to open it and review it before treating it as final;
   publishing never changes the campaign files, so they fix things in the
   campaign and publish again.
   - If the result has a `note` that `published/` is not in `.gitignore`,
     offer to add it, so snapshots don't commit the PDFs.
   - Suggest saving the publishing details with `/save-campaign`, and, in
     git, tagging the commit with the edition, such as `edition-1.0`.
