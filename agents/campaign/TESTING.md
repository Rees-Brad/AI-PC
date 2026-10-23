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
- The encounter starts with a summary: each creature's CR and XP, the
  total XP and XP per character, and a difficulty for the party.
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

### 8. Collections and epics

1. Create a folder, run `git init` in it, open it in VS Code, and run
   `/create-collection`. Create two subfolders and run `/create-campaign`
   in each.
2. Change a file in each campaign, then run `/save-campaign` in just one.
3. Run `/start-campaign` for "Test Group" in that campaign.
4. In a new folder (with `git init`), run `/create-epic`. Create two book
   subfolders, run `/create-campaign` in each, and let the agent add them
   to `epic.md`.
5. In Book 1's `npcs.md`, give an NPC the status "dies"; add the same NPC
   to Book 2's `npcs.md`. Run `/check-epic`.

Check:
- Saving one campaign committed only that campaign; the other's change is
  still uncommitted.
- The running copy is a sibling folder in the same repository, committed
  there.
- Books took the epic's rules edition without asking.
- `/check-epic` reports the NPC who dies in Book 1 but appears in Book 2,
  and the agent adds its own story review.

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
