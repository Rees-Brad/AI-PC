import random

import pytest

from ai_pc.rules_engine.dnd5e.dice import roll


def test_roll_deterministic_with_seeded_rng():
    result = roll("2d6+3", rng=random.Random(42))
    assert len(result.rolls) == 2
    assert all(1 <= r <= 6 for r in result.rolls)
    assert result.modifier == 3
    assert result.total == sum(result.rolls) + 3


def test_roll_single_die_default_count():
    result = roll("d20")
    assert len(result.rolls) == 1
    assert 1 <= result.rolls[0] <= 20
    assert result.modifier == 0


def test_roll_negative_modifier():
    result = roll("1d8-1", rng=random.Random(1))
    assert result.modifier == -1
    assert result.total == result.rolls[0] - 1


def test_roll_invalid_expression_raises():
    with pytest.raises(ValueError):
        roll("not-dice")
