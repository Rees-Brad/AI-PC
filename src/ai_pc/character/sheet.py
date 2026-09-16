from enum import Enum

from pydantic import BaseModel, Field


class Ability(str, Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"


class AbilityScores(BaseModel):
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def modifier(self, ability: Ability) -> int:
        score = getattr(self, ability.value)
        return (score - 10) // 2


class SpellSlots(BaseModel):
    # level (1-9) -> (current, max)
    max_by_level: dict[int, int] = Field(default_factory=dict)
    current_by_level: dict[int, int] = Field(default_factory=dict)


class InventoryItem(BaseModel):
    name: str
    quantity: int = 1
    equipped: bool = False
    notes: str = ""


class Condition(BaseModel):
    name: str
    duration: str | None = None  # free-form, e.g. "1 minute", "until save"


class CharacterSheet(BaseModel):
    name: str
    character_class: str
    race: str = ""
    gender: str = ""
    alignment: str = ""
    level: int = 1
    background: str = ""
    persona: str = ""  # personality/voice, fed into the system prompt

    abilities: AbilityScores = Field(default_factory=AbilityScores)
    proficiency_bonus: int = 2
    proficient_skills: list[str] = Field(default_factory=list)
    proficient_saves: list[Ability] = Field(default_factory=list)

    max_hp: int = 1
    current_hp: int = 1
    temp_hp: int = 0
    armor_class: int = 10

    spell_slots: SpellSlots = Field(default_factory=SpellSlots)
    known_spells: list[str] = Field(default_factory=list)

    inventory: list[InventoryItem] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)

    features: list[str] = Field(default_factory=list)

    def ability_modifier(self, ability: Ability) -> int:
        return self.abilities.modifier(ability)

    def saving_throw_modifier(self, ability: Ability) -> int:
        mod = self.ability_modifier(ability)
        if ability in self.proficient_saves:
            mod += self.proficiency_bonus
        return mod
