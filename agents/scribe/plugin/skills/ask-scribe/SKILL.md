---
name: ask-scribe
description: Answer the DM's questions about what has happened in play from the Scribe's record - past sessions, recaps, plot threads, NPCs, locations, factions, promises the party made, who knows what, and the DM's private notes. Use when the DM asks what happened, who someone is, what the party knows, or anything about earlier game sessions.
argument-hint: "[question]"
---

# Ask the Scribe

The Scribe keeps the record of what actually happened at the table. Answer
the DM's question from that record: $ARGUMENTS

## Finding the record

- If the current folder is a Campaign Agent running copy (it has
  `.campaign/campaign.json` with `"role": "running"`), pass its absolute path
  as `campaign_folder` to every Scribe tool.
- Otherwise call the tools without `campaign_folder`; the Scribe uses its
  configured database.
- A master campaign has no Scribe record. Games are recorded in running
  copies.

## Answering

1. Choose the tool that fits: `recap` and `list_sessions` for what happened
   when, `lookup` for an NPC, location, or faction, `open_threads` for
   unresolved hooks and promises, `who_knows` for which characters know
   something, `dm_notes` for the DM's private notes, and `search_record`
   for anything else.
2. Answer only from what the tools return. Say which session something
   happened in when the record shows it. If the record says something was
   unclear or inaudible, say so.
3. If the record has nothing on the question, say that plainly. Do not fill
   the gap with a guess or with the campaign's plans: planned events are
   not events that happened.
4. Awareness ("who knows what") is inferred from play and can be wrong.
   Present it as the Scribe's best reading.
5. Answers are for the DM only. Mark anything from the DM's private notes as
   private, so the DM knows not to read it out to the players.
6. Never change the record. Corrections go through the Scribe's DM commands
   in Discord.
