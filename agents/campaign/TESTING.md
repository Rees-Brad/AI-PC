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
- The agent explained the master/running-copy split.
- You were asked to approve file changes before they were written.

### 2. Resume

1. Close the conversation, start a new one in the same folder, and run
   `/create-campaign` again.

Check: the agent summarizes where the campaign stands instead of starting
over.

### 3. Maps

1. Save a PNG or JPEG map into `maps/`.
2. Ask the agent to add it to an adventure, then ask it a question about
   the map.

Check:
- The map shows in the adventure's Markdown preview.
- The answer uses what's on the map, and the agent says when it can't read
  something rather than guessing.

### 4. Restructure

1. Ask the agent to move an adventure to the other chapter, then to drop an
   encounter.

Check:
- The agent lists what it will change before doing it, and asks before
  dropping anything.
- Afterwards `/check-campaign` reports no broken links, and the indexes
  point to the new locations.

### 5. Check

1. Break something by hand: rename an adventure file, add an unlinked
   image to `maps/`, or add an index entry with no link.
2. Run `/check-campaign`.

Check: each problem is reported with a clickable file, and nothing is
changed until you agree to a fix.

### 6. Start a running copy

1. In the master, run `/start-campaign` for a group called "Test Group".
2. Try it again after making an uncommitted change to the master.
3. Open the running copy and run `/start-campaign` there.

Check:
- The first run creates `<master>--test-group` next to the master, with a
  `sessions/` folder, and the master is unchanged.
- The second run refuses until the change is committed.
- The third run refuses because it is already a running copy.

### 7. Starting material (optional)

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
