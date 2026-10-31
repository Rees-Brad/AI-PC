"""Encounter arithmetic: XP by Challenge Rating, and difficulty for a party.

The agent writes each encounter's summary from these numbers rather than doing the
arithmetic itself. D&D 5e uses XP by Challenge Rating and, for the 2024 rules, XP
budgets. D&D 3.5 uses Encounter Level against the party's level, and awards XP by
each character's level. Verify the tables against the rules before publishing.
"""

from __future__ import annotations

import math
from fractions import Fraction

from ai_campaign import systems

# XP for a creature of each Challenge Rating (the same in the 2014 and 2024 rules).
XP_BY_CR: dict[Fraction, int] = {
    Fraction(0): 10,
    Fraction(1, 8): 25,
    Fraction(1, 4): 50,
    Fraction(1, 2): 100,
    **{
        Fraction(cr): xp
        for cr, xp in {
            1: 200, 2: 450, 3: 700, 4: 1100, 5: 1800, 6: 2300, 7: 2900, 8: 3900, 9: 5000,
            10: 5900, 11: 7200, 12: 8400, 13: 10000, 14: 11500, 15: 13000, 16: 15000,
            17: 18000, 18: 20000, 19: 22000, 20: 25000, 21: 33000, 22: 41000, 23: 50000,
            24: 62000, 25: 75000, 26: 90000, 27: 105000, 28: 120000, 29: 135000, 30: 155000,
        }.items()
    },
}

# D&D 5e (2024): XP budget per character for Low, Moderate, and High difficulty.
BUDGET_2024: dict[int, tuple[int, int, int]] = {
    1: (50, 75, 100), 2: (100, 150, 200), 3: (150, 225, 400), 4: (250, 375, 500),
    5: (500, 750, 1100), 6: (600, 1000, 1400), 7: (750, 1300, 1700), 8: (1000, 1700, 2100),
    9: (1300, 2000, 2600), 10: (1600, 2300, 3100), 11: (1900, 2900, 4100),
    12: (2200, 3700, 4700), 13: (2600, 4200, 5400), 14: (2900, 4900, 6200),
    15: (3300, 5400, 7800), 16: (3800, 6100, 9800), 17: (4500, 7200, 11700),
    18: (5000, 8700, 14200), 19: (5500, 10700, 17200), 20: (6400, 13200, 22000),
}
DIFFICULTIES = ("Low", "Moderate", "High")


# D&D 3.5 Challenge Ratings below 1.
FRACTIONAL_CR_3_5 = tuple(Fraction(1, n) for n in (10, 8, 6, 4, 3, 2))
DIFFICULTIES_3_5 = ("Easy", "Challenging", "Very difficult", "Overpowering")


def parse_cr(value: str | int | float, rules: str = systems.DND_5E_2024) -> Fraction:
    text = str(value).strip().lower().removeprefix("cr").strip()
    try:
        cr = Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"'{value}' is not a Challenge Rating.") from error
    if systems.rules_family(rules) == systems.DND_3_5:
        if cr not in FRACTIONAL_CR_3_5 and not (cr >= 1 and cr.denominator == 1):
            raise ValueError(
                f"'{value}' is not a D&D 3.5 Challenge Rating (use 1/10, 1/8, 1/6, 1/4, 1/3, "
                "1/2, or a whole number from 1)."
            )
        return cr
    if cr not in XP_BY_CR:
        raise ValueError(f"'{value}' is not a Challenge Rating (use 0, 1/8, 1/4, 1/2, or 1-30).")
    return cr


def _cr_label(cr: Fraction) -> str:
    return str(cr.numerator) if cr.denominator == 1 else f"{cr.numerator}/{cr.denominator}"


def encounter_xp(
    creatures: list[dict[str, object]], party_levels: list[int], rules: str = "D&D 5e (2024)"
) -> dict[str, object]:
    """Total XP, XP per character, and difficulty for one encounter.

    `creatures` is a list of {"name", "cr", "count"}; `party_levels` lists each
    character's level. Difficulty is rated with the 2024 XP budgets; for other rules
    editions only the XP is calculated.
    """
    if not creatures:
        raise ValueError("List at least one creature.")
    if not party_levels or any(not 1 <= int(level) <= 20 for level in party_levels):
        raise ValueError("Give each character's level, from 1 to 20.")
    if systems.rules_family(rules) == systems.DND_3_5:
        return encounter_3_5(creatures, [int(level) for level in party_levels])

    rows = []
    total = 0
    for creature in creatures:
        cr, count = _creature(creature, rules)
        xp = XP_BY_CR[cr]
        rows.append({
            "name": str(creature.get("name", "Creature")),
            "cr": _cr_label(cr),
            "count": count,
            "xp_each": xp,
            "xp_total": xp * count,
        })
        total += xp * count

    party = len(party_levels)
    result: dict[str, object] = {
        "creatures": rows,
        "total_xp": total,
        "party_size": party,
        "xp_per_character": total // party,
    }
    if "2024" in rules or "5.2" in rules:
        budgets = [sum(BUDGET_2024[int(level)][i] for level in party_levels) for i in range(3)]
        result["budgets"] = dict(zip(DIFFICULTIES, budgets))
        if total <= budgets[0]:
            rating = "Low"
        elif total <= budgets[1]:
            rating = "Moderate"
        elif total <= budgets[2]:
            rating = "High"
        else:
            rating = "Beyond High (very dangerous)"
        result["difficulty"] = rating
    else:
        result["difficulty"] = (
            f"Not rated: difficulty here uses the 2024 XP budgets, and this campaign uses "
            f"{rules}. Rate it with that edition's encounter rules."
        )
    return result


def _creature(creature: dict[str, object], rules: str) -> tuple[Fraction, int]:
    cr = parse_cr(str(creature.get("cr", "")), rules)
    count = int(str(creature.get("count", 1)))
    if count < 1:
        raise ValueError("Each creature's count must be at least 1.")
    return cr, count


def _power_3_5(cr: Fraction) -> float:
    """A creature's share of an Encounter Level: two of a CR make that CR + 2."""
    return float(cr) * math.sqrt(2) if cr < 1 else 2 ** (float(cr) / 2)


def encounter_level_3_5(creatures: list[tuple[Fraction, int]]) -> Fraction:
    """D&D 3.5 Encounter Level for a group of (CR, count)."""
    total = sum(_power_3_5(cr) * count for cr, count in creatures)
    if total < math.sqrt(2):  # weaker than one CR 1 creature
        below_one = total / math.sqrt(2)
        return min(FRACTIONAL_CR_3_5, key=lambda cr: abs(float(cr) - below_one))
    return Fraction(max(1, round(2 * math.log2(total))))


def party_level_3_5(levels: list[int]) -> int:
    """Average level, plus one for six or more characters, minus one for three or fewer."""
    average = math.floor(sum(levels) / len(levels) + 0.5)
    if len(levels) >= 6:
        average += 1
    elif len(levels) <= 3:
        average -= 1
    return max(1, average)


def xp_award_3_5(level: int, cr: Fraction) -> int | None:
    """XP one character of `level` earns for defeating one creature, before sharing.

    An approximation of the Dungeon Master's Guide award table: 300 x level, doubled
    for every 2 CR above the level and halved for every 2 below. None when the CR is
    more than 7 above the level (off the table; the DM decides).
    """
    if cr < 1:
        award = xp_award_3_5(level, Fraction(1))
        return round((award or 0) * float(cr))
    difference = int(cr) - level
    if difference < -7:
        return 0
    if difference > 7:
        return None
    return int(round(300 * level * 2 ** (difference / 2) / 25) * 25)


def encounter_3_5(creatures: list[dict[str, object]], party_levels: list[int]) -> dict[str, object]:
    rows = []
    parsed = []
    for creature in creatures:
        cr, count = _creature(creature, systems.DND_3_5)
        parsed.append((cr, count))
        rows.append({
            "name": str(creature.get("name", "Creature")),
            "cr": _cr_label(cr),
            "count": count,
        })
    level = encounter_level_3_5(parsed)
    party_level = party_level_3_5(party_levels)
    if level < party_level:
        rating = DIFFICULTIES_3_5[0]
    elif level == party_level:
        rating = DIFFICULTIES_3_5[1]
    elif level <= party_level + 4:
        rating = DIFFICULTIES_3_5[2]
    else:
        rating = DIFFICULTIES_3_5[3]

    awards = []
    off_table = False
    for character_level in party_levels:
        total = 0
        for cr, count in parsed:
            award = xp_award_3_5(character_level, cr)
            if award is None:
                off_table = True
                award = 0
            total += award * count
        awards.append({"level": character_level, "xp": total // len(party_levels)})

    result: dict[str, object] = {
        "rules": systems.DND_3_5,
        "creatures": rows,
        "encounter_level": _cr_label(level),
        "party_size": len(party_levels),
        "party_level": party_level,
        "difficulty": rating,
        "xp_by_character": awards,
        "xp_note": (
            "XP is an approximation of the Dungeon Master's Guide award table; check it "
            "there, especially for levels 1-3 and odd CR differences. The DM decides."
        ),
    }
    if off_table:
        result["xp_note"] = (
            f"{result['xp_note']} Some creatures are more than 7 CR above a character's "
            "level, which is off the table, so they are counted as 0 here."
        )
    return result
