# Testing the Campaign Agent

Thanks for testing. Install the plugin by following the
[README](README.md), then work through the scenarios below in VS Code.
Each takes a few minutes. Use throwaway folders; nothing here touches
anything outside the folders you choose.

## Scenarios

### 1. Create a campaign

1. Open an empty folder in VS Code and run `/create-campaign`.
2. Give it a title, and say yes to git.
3. Develop a small campaign with the agent: a goal, two chapters, and at
   least one adventure and one encounter in each chapter. Mention a few key
   NPCs, a magic item, and a location or two.

Check:
- Each chapter, adventure, and encounter is its own file, under
  `chapters/NN-name/`.
- `campaign.md` links every chapter, and each `chapter.md` links its
  adventures and encounters.
- Key NPCs, items, and locations appear in `npcs.md`, `items.md`, and
  `locations.md`, each linking to where they appear.
- The agent pointed you to `GETTING_STARTED.md` rather than a long
  welcome in the chat, and it reads well in the Markdown preview.
- `campaign.md` records D&D 5e (2024) in its Rules section.
- Questions the agent raised appear in `OPEN_ITEMS.md`, and are checked off
  when settled.
- You were asked to approve file changes before they were written.

### 2. Encounters

1. Open one of the encounter files.

Check:
- Every creature has a full stat block, not just a name like "thug".
- Named NPCs who fight have their own stat block.
- The file ends with an encounter tracker table with a row per creature,
  and it prints sensibly from the Markdown preview.

### 3. Save and resume

1. Mark one item in `OPEN_ITEMS.md` **(priority)**, then run
   `/save-campaign`.
2. Close VS Code, reopen the folder, start a new conversation, and run
   `/create-campaign`.

Check:
- `/save-campaign` added a dated `WORKLOG.md` entry and took a snapshot
  (a git commit, or a zip in `.campaign/snapshots/` without git).
- On resume, the agent summarizes where things stood and suggests starting
  with your priority item, instead of starting over.
- The earlier conversation can be reopened from the past conversations
  button in the Claude Code panel.

### 4. Maps

1. Save a PNG or JPEG map into `maps/`.
2. Ask the agent to add it to an adventure, then ask it a question about
   the map.

Check:
- The map shows in the adventure's Markdown preview.
- The answer uses what's on the map, and the agent says when it can't read
  something rather than guessing.

### 5. Restructure

1. Ask the agent to move an adventure to the other chapter, then to drop an
   encounter.

Check:
- The agent lists what it will change before doing it, and asks before
  dropping anything.
- Afterwards `/check-campaign` reports no broken links, and the indexes
  point to the new locations.

### 6. Check

1. Break something by hand: rename an adventure file, add an unlinked
   image to `maps/`, or add an index entry with no link.
2. Run `/check-campaign`.

Check: each problem is reported with a clickable file, and nothing is
changed until you agree to a fix.

### 7. Start a running copy

1. In the master, run `/start-campaign` for a group called "Test Group".
2. Try it again after making an uncommitted change to the master.
3. Open the running copy and run `/start-campaign` there.

Check:
- The first run creates `<master>--test-group` next to the master, with a
  `sessions/` folder, and the master is unchanged.
- The second run refuses until the change is committed.
- The third run refuses because it is already a running copy.

### 8. Collections

1. In an empty folder, run `/create-collection`.
2. Inside it, open a new empty folder and run `/create-campaign`; choose to
   add it to the collection. Add a chapter.
3. Run `/save-campaign`, then `/start-campaign` for "Test Group".
4. Edit a file in the running copy and run `/save-campaign` there.

Check:
- The collection's Source Control view lists the campaign and the running
  copy as submodules, and nothing is left uncommitted.
- Saving the running copy committed the running copy and the collection's
  record of it.

### 9. Another rules edition (optional)

1. In a new empty folder, run `/create-campaign` and ask for D&D 5e (2014).

Check: `campaign.md` records the 2014 edition with the SRD 5.1 attribution,
and stat blocks follow that edition.

### 10. Starting material (optional)

1. In a new empty folder, run `/create-campaign` and give the agent a text
   file or a PDF with selectable text as starting notes.

Check: the agent uses the material. A scanned PDF with no text layer should
be refused with a clear message.

## Reporting

For each problem, please send:
- the scenario and what you asked the agent;
- what happened, and what you expected;
- any error message, exactly as shown;
- your OS, VS Code version, and Claude Code extension version.

Opinions are useful too: questions the agent should have asked, files laid
out in a way you didn't expect, or wording that confused you.
