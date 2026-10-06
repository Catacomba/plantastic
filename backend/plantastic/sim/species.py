"""Plant species: how tips grow and how a plant responds to a cut.

Rules receive the world so that later species can react to their surroundings.
Any randomness a rule needs must come from ``world.rng``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from .hex import Hex, direction_between, turn_left, turn_right

if TYPE_CHECKING:
    from .world import Plant, Tip, World


class Species:
    id: str
    name: str
    default_speed: Fraction

    def grow(self, tip: Tip, world: World) -> list[int]:
        """Headings the tip continues with when it is due to advance.

        One heading continues the tip, several branch it, none ends it.
        """
        raise NotImplementedError

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[tuple[Hex, int]]:
        """New tips to create after a cut, as (cell, heading) pairs."""
        raise NotImplementedError


class StraightVine(Species):
    id = "straight-vine"
    name = "Straight vine"
    default_speed = Fraction(1)

    def grow(self, tip: Tip, world: World) -> list[int]:
        return [tip.heading]

    def on_cut(self, plant: Plant, stump: Hex, world: World) -> list[tuple[Hex, int]]:
        # Walk two cells back toward the root, stopping early at the root.
        sprout = stump
        toward_stump = stump
        for _ in range(2):
            parent = world.cells[sprout].parent
            if parent is None:
                break
            toward_stump = sprout
            sprout = parent
        forward = direction_between(sprout, toward_stump)
        return [
            (sprout, heading)
            for heading in (turn_left(forward), turn_right(forward))
            if world.can_sprout(plant, sprout, heading)
        ]


CATALOG: dict[str, Species] = {species.id: species for species in (StraightVine(),)}
