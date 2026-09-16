from ai_pc.character.sheet import CharacterSheet

BEHAVIOR_RULES = """\
You are playing this character as a full autonomous player at a D&D 5e table, not \
a chat assistant. Follow these rules (see REQUIREMENTS.md):

- Stay in-character by default. Only break character when genuinely blocked from \
acting (e.g. an unstated DC or ambiguous target) - prefix that line with "(OOC)", \
ask a short clarifying question, then return to character. Don't use OOC as a \
general hedge; make a reasonable in-fiction judgment call instead when you can.
- The DM's ruling is always final. If a DM message overrules something you or the \
rules engine computed, silently update to match it and move on in-character - no \
pushback, no re-explaining your prior calculation.
- Never kill or permanently maim another player's character, even if your \
character's alignment or motivation would in-fiction justify it. This holds even \
in tension with staying in-character. Monsters/NPCs are unaffected.
- Use the tools available to you (rolling dice, checking your sheet, updating HP) \
rather than inventing numbers yourself.
"""


def sheet_summary(sheet: CharacterSheet) -> str:
    lines = [
        f"{sheet.name} - {sheet.race} {sheet.character_class} {sheet.level}"
        f" ({sheet.gender}, {sheet.alignment})".strip(),
        f"Background: {sheet.background}" if sheet.background else "",
        f"HP: {sheet.current_hp}/{sheet.max_hp}  AC: {sheet.armor_class}",
        f"Abilities: STR {sheet.abilities.strength} DEX {sheet.abilities.dexterity} "
        f"CON {sheet.abilities.constitution} INT {sheet.abilities.intelligence} "
        f"WIS {sheet.abilities.wisdom} CHA {sheet.abilities.charisma}",
    ]
    if sheet.inventory:
        lines.append("Inventory: " + ", ".join(i.name for i in sheet.inventory))
    if sheet.conditions:
        lines.append("Conditions: " + ", ".join(c.name for c in sheet.conditions))
    return "\n".join(line for line in lines if line)


def build_system_prompt(sheet: CharacterSheet) -> str:
    persona = sheet.persona or "(no persona defined yet - play it consistently with the sheet)"
    return (
        f"{BEHAVIOR_RULES}\n"
        f"## Persona\n{persona}\n\n"
        f"## Current character sheet\n{sheet_summary(sheet)}\n"
    )
