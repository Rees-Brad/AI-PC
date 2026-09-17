from anthropic import beta_tool
from sqlalchemy.orm import sessionmaker

from ai_pc.llm.prompts import sheet_summary
from ai_pc_shared.persistence.repository import load_character_sheet, save_character_sheet
from ai_pc_shared.rules_engine.dnd5e.dice import roll as roll_dice_expr


def build_tools(character_name: str, session_factory: sessionmaker) -> list:
    """Build the Claude tool set for a specific character, bound to a session factory."""

    @beta_tool
    def get_character_sheet() -> str:
        """Get this character's full current sheet: abilities, HP, AC, inventory, conditions."""
        with session_factory() as session:
            sheet = load_character_sheet(session, character_name)
        if sheet is None:
            return "No character sheet found."
        return sheet_summary(sheet)

    @beta_tool
    def roll_dice(expression: str) -> str:
        """Roll dice using standard notation for narrative or ad-hoc rolls.

        Args:
            expression: Dice expression, e.g. "1d20+5", "2d6", "1d8-1".
        """
        result = roll_dice_expr(expression)
        return f"Rolled {expression}: {result.rolls} + {result.modifier} = {result.total}"

    @beta_tool
    def update_hp(delta: int, reason: str) -> str:
        """Change this character's current HP and persist it. Use this for all HP changes.

        Args:
            delta: Amount to change current HP by. Negative for damage, positive for healing.
            reason: Short reason for the change, e.g. "hit by a goblin's arrow".
        """
        with session_factory() as session:
            sheet = load_character_sheet(session, character_name)
            if sheet is None:
                return "No character sheet found."
            sheet.current_hp = max(0, min(sheet.max_hp, sheet.current_hp + delta))
            save_character_sheet(session, sheet)
            new_hp = sheet.current_hp
        return f"HP changed by {delta} ({reason}). Current HP: {new_hp}/{sheet.max_hp}."

    return [get_character_sheet, roll_dice, update_hp]
