from __future__ import annotations

import pytest

from ai_campaign.encounters import encounter_xp, parse_cr


def test_xp_and_2024_difficulty() -> None:
    result = encounter_xp(
        [{"name": "Bandit", "cr": "1/8", "count": 4}, {"name": "Thug", "cr": 1, "count": 1}],
        [2, 2, 2, 2],
    )
    assert result["total_xp"] == 300
    assert result["xp_per_character"] == 75
    assert result["creatures"][0] == {
        "name": "Bandit", "cr": "1/8", "count": 4, "xp_each": 25, "xp_total": 100,
    }
    assert result["budgets"] == {"Low": 400, "Moderate": 600, "High": 800}
    assert result["difficulty"] == "Low"


@pytest.mark.parametrize(
    "count, rating", [(2, "Low"), (3, "Moderate"), (4, "High"), (5, "Beyond High (very dangerous)")]
)
def test_difficulty_bands(count: int, rating: str) -> None:
    # Party of four level 1 characters: budgets 200 / 300 / 400.
    result = encounter_xp([{"name": "Wolf", "cr": "1/4", "count": count * 2}], [1, 1, 1, 1])
    assert result["difficulty"] == rating


def test_other_editions_get_xp_but_no_rating() -> None:
    result = encounter_xp([{"name": "Ogre", "cr": "2"}], [3, 3], rules="D&D 5e (2014)")
    assert result["total_xp"] == 450 and result["xp_per_character"] == 225
    assert result["difficulty"].startswith("Not rated")
    assert "budgets" not in result


@pytest.mark.parametrize("value", ["CR 1/2", "0", "30", 5])
def test_parse_cr_accepts_valid_ratings(value: object) -> None:
    parse_cr(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "creatures, levels, message",
    [
        ([], [1], "at least one creature"),
        ([{"cr": "1/3"}], [1], "not a Challenge Rating"),
        ([{"cr": "1", "count": 0}], [1], "at least 1"),
        ([{"cr": "1"}], [], "each character's level"),
        ([{"cr": "1"}], [21], "each character's level"),
    ],
)
def test_bad_input_is_explained(creatures: list, levels: list, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        encounter_xp(creatures, levels)
