import anthropic
from pydantic import BaseModel, Field

from ai_pc.config import Settings
from ai_pc_shared.character.sheet import AbilityScores, CharacterSheet, InventoryItem


class CreationConstraints(BaseModel):
    """DM-set constraints for AI-driven character creation (REQUIREMENTS.md, path 1).

    Anything left unset is the AI's call.
    """

    class_suggestion: str | None = None
    alignment: str | None = None
    allowed_races: list[str] | None = None
    allowed_genders: list[str] | None = None
    starting_level: int = 1
    ability_score_method: str = "standard array (15, 14, 13, 12, 10, 8, assign as you like)"
    name_override: str | None = None


class GeneratedCharacter(BaseModel):
    name: str
    race: str
    gender: str
    alignment: str
    character_class: str
    level: int
    background: str
    persona: str = Field(description="Personality, speech pattern, combat temperament")
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    max_hp: int
    armor_class: int
    proficient_skills: list[str]
    known_spells: list[str] = Field(default_factory=list)
    starting_equipment: list[str]


def proficiency_bonus_for_level(level: int) -> int:
    return 2 + (max(level, 1) - 1) // 4


def _build_prompt(constraints: CreationConstraints) -> str:
    lines = [
        "Create a new D&D 5e player character for an AI-backed autonomous player.",
        "You are free to decide anything not constrained below.",
        f"- Starting level: {constraints.starting_level}",
        f"- Ability score generation method: {constraints.ability_score_method}",
    ]
    if constraints.class_suggestion:
        lines.append(f"- Class: the DM suggests/requires {constraints.class_suggestion}")
    if constraints.alignment:
        lines.append(f"- Alignment: must be {constraints.alignment}")
    if constraints.allowed_races:
        lines.append(f"- Race: must be one of {', '.join(constraints.allowed_races)}")
    if constraints.allowed_genders:
        lines.append(f"- Gender: must be one of {', '.join(constraints.allowed_genders)}")
    if constraints.name_override:
        lines.append(f"- Name: must be {constraints.name_override}")
    lines.append(
        "Compute max_hp and armor_class yourself using standard 5e rules for the "
        "chosen class/level/Constitution/Dexterity. Give a concise but vivid persona "
        "(personality, speech pattern, combat temperament) and a short background."
    )
    return "\n".join(lines)


def sheet_from_generated(generated: GeneratedCharacter) -> CharacterSheet:
    """Map a GeneratedCharacter (Claude's structured output) onto a CharacterSheet."""
    return CharacterSheet(
        name=generated.name,
        character_class=generated.character_class,
        race=generated.race,
        gender=generated.gender,
        alignment=generated.alignment,
        level=generated.level,
        background=generated.background,
        persona=generated.persona,
        abilities=AbilityScores(
            strength=generated.strength,
            dexterity=generated.dexterity,
            constitution=generated.constitution,
            intelligence=generated.intelligence,
            wisdom=generated.wisdom,
            charisma=generated.charisma,
        ),
        proficiency_bonus=proficiency_bonus_for_level(generated.level),
        proficient_skills=generated.proficient_skills,
        max_hp=generated.max_hp,
        current_hp=generated.max_hp,
        armor_class=generated.armor_class,
        known_spells=generated.known_spells,
        inventory=[InventoryItem(name=item) for item in generated.starting_equipment],
    )


def create_character(
    client: anthropic.Anthropic, settings: Settings, constraints: CreationConstraints
) -> CharacterSheet:
    response = client.messages.parse(
        model=settings.ai_pc_model,
        max_tokens=4000,
        messages=[{"role": "user", "content": _build_prompt(constraints)}],
        output_format=GeneratedCharacter,
    )
    if response.parsed_output is None:
        raise RuntimeError(
            f"Claude did not return a structured character (stop_reason={response.stop_reason!r})"
        )
    return sheet_from_generated(response.parsed_output)
