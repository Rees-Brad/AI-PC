from ai_pc.character.creation import (
    GeneratedCharacter,
    proficiency_bonus_for_level,
    sheet_from_generated,
)


def _sample_generated(**overrides) -> GeneratedCharacter:
    defaults = dict(
        name="Ashra Windfall",
        race="Half-Elf",
        gender="Female",
        alignment="Chaotic Good",
        character_class="Bard",
        level=1,
        background="Wandering minstrel",
        persona="Quick-witted, flirtatious, bold with words.",
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=10,
        wisdom=10,
        charisma=17,
        max_hp=9,
        armor_class=13,
        proficient_skills=["Persuasion", "Performance"],
        known_spells=["Vicious Mockery", "Healing Word"],
        starting_equipment=["Rapier", "Lute", "Leather Armor"],
    )
    defaults.update(overrides)
    return GeneratedCharacter(**defaults)


def test_proficiency_bonus_by_level():
    assert proficiency_bonus_for_level(1) == 2
    assert proficiency_bonus_for_level(4) == 2
    assert proficiency_bonus_for_level(5) == 3
    assert proficiency_bonus_for_level(9) == 4
    assert proficiency_bonus_for_level(13) == 5
    assert proficiency_bonus_for_level(17) == 6
    assert proficiency_bonus_for_level(20) == 6


def test_sheet_from_generated_maps_all_fields():
    generated = _sample_generated()
    sheet = sheet_from_generated(generated)

    assert sheet.name == "Ashra Windfall"
    assert sheet.character_class == "Bard"
    assert sheet.race == "Half-Elf"
    assert sheet.gender == "Female"
    assert sheet.alignment == "Chaotic Good"
    assert sheet.proficiency_bonus == proficiency_bonus_for_level(generated.level)
    assert sheet.abilities.charisma == 17
    assert sheet.max_hp == sheet.current_hp == 9
    assert [item.name for item in sheet.inventory] == ["Rapier", "Lute", "Leather Armor"]
    assert sheet.known_spells == ["Vicious Mockery", "Healing Word"]


def test_sheet_from_generated_high_level_proficiency_bonus():
    generated = _sample_generated(level=9)
    sheet = sheet_from_generated(generated)
    assert sheet.proficiency_bonus == 4
