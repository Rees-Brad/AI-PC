"""Encounter arithmetic: XP by Challenge Rating, and difficulty for a party.

The agent writes each encounter's summary from these numbers rather than doing the
arithmetic itself. The tables follow the D&D 5e rules; verify them against the
System Reference Document before publishing a campaign.
"""

from __future__ import annotations

from fractions import Fraction

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


def parse_cr(value: str | int | float) -> Fraction:
    text = str(value).strip().lower().removeprefix("cr").strip()
    try:
        cr = Fraction(text)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError(f"'{value}' is not a Challenge Rating.") from error
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

    rows = []
    total = 0
    for creature in creatures:
        cr = parse_cr(str(creature.get("cr", "")))
        count = int(str(creature.get("count", 1)))
        if count < 1:
            raise ValueError("Each creature's count must be at least 1.")
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
