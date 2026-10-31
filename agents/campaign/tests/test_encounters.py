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


def test_3_5_encounter_level_and_difficulty() -> None:
    result = encounter_xp([{"name": "Orc", "cr": "1/2", "count": 4}], [1, 1, 1, 1], "D&D 3.5")
    assert result["encounter_level"] == "3"  # four CR 1/2 = two CR 1 = EL 3
    assert result["party_level"] == 1
    assert result["difficulty"] == "Very difficult"
    assert result["xp_by_character"] == [{"level": 1, "xp": 150}] * 4
    assert "budgets" not in result


@pytest.mark.parametrize(
    "creatures, level",
    [
        ([("3", 1)], "3"),
        ([("3", 2)], "5"),  # doubling the creatures adds 2
        ([("3", 4)], "7"),
        ([("1/3", 1)], "1/3"),
        ([("1/2", 2)], "1"),
        ([("5", 1), ("3", 2)], "7"),  # two CR 3 are EL 5; with a CR 5, EL 7
    ],
)
def test_3_5_encounter_levels(creatures: list, level: str) -> None:
    listed = [{"cr": cr, "count": count} for cr, count in creatures]
    assert encounter_xp(listed, [5, 5, 5, 5], "D&D 3.5")["encounter_level"] == level


@pytest.mark.parametrize(
    "el_cr, rating", [("4", "Easy"), ("5", "Challenging"), ("9", "Very difficult"),
                      ("10", "Overpowering")]
)
def test_3_5_difficulty_bands(el_cr: str, rating: str) -> None:
    assert encounter_xp([{"cr": el_cr}], [5, 5, 5, 5], "D&D 3.5")["difficulty"] == rating


def test_3_5_party_level_adjusts_for_party_size() -> None:
    small = encounter_xp([{"cr": "4"}], [4, 4, 4], "D&D 3.5")
    large = encounter_xp([{"cr": "4"}], [4] * 6, "D&D 3.5")
    assert small["party_level"] == 3 and small["difficulty"] == "Very difficult"
    assert large["party_level"] == 5 and large["difficulty"] == "Easy"


def test_3_5_xp_awards_follow_each_characters_level() -> None:
    result = encounter_xp([{"cr": "4"}], [4, 4, 6, 6], "D&D 3.5")
    # 300 x level at the same CR; halved for every 2 CR below the level.
    assert result["xp_by_character"] == [
        {"level": 4, "xp": 300}, {"level": 4, "xp": 300},
        {"level": 6, "xp": 225}, {"level": 6, "xp": 225},
    ]
    far = encounter_xp([{"cr": "1"}, {"cr": "20"}], [10], "D&D 3.5")
    assert far["xp_by_character"] == [{"level": 10, "xp": 0}]
    assert "off the table" in str(far["xp_note"])


def test_3_5_challenge_ratings() -> None:
    assert parse_cr("1/3", "D&D 3.5") == parse_cr("1/3", "3.5e")
    assert parse_cr("40", "D&D 3.5") == 40
    with pytest.raises(ValueError, match="3.5 Challenge Rating"):
        parse_cr("0", "D&D 3.5")
    with pytest.raises(ValueError, match="not a Challenge Rating"):
        parse_cr("1/3")  # not a 5e rating
