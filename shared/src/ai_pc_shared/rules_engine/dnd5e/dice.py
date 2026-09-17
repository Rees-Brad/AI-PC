import random
import re

from pydantic import BaseModel

_DICE_RE = re.compile(r"^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)


class RollResult(BaseModel):
    expression: str
    rolls: list[int]
    modifier: int
    total: int


def roll(expression: str, rng: random.Random | None = None) -> RollResult:
    """Roll a dice expression like "1d20+5", "2d6", or "d8-1"."""
    match = _DICE_RE.match(expression)
    if not match:
        raise ValueError(f"Invalid dice expression: {expression!r}")

    rng = rng or random.Random()
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    modifier = int(match.group(3).replace(" ", "")) if match.group(3) else 0

    if count < 1 or sides < 1:
        raise ValueError(f"Invalid dice expression: {expression!r}")

    rolls = [rng.randint(1, sides) for _ in range(count)]
    return RollResult(
        expression=expression, rolls=rolls, modifier=modifier, total=sum(rolls) + modifier
    )
