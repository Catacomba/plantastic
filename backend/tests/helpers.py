from plantastic.sim.species import CATALOG, Shoot, Species
from plantastic.sim.world import World

VINE = "straight-vine"
EAST, SOUTH_EAST, SOUTH_WEST, WEST, NORTH_WEST, NORTH_EAST = range(6)


class Persistent(Species):
    """A straight grower with a chosen persistence."""

    id = "persistent"
    name = "Persistent"

    def __init__(self, persistence: int = 100):
        self.persistence = persistence


class Circler(Persistent):
    """Turns right on every step, so it runs around a ring and into its own root."""

    id = "circler"
    name = "Circler"

    def grow(self, tip, plant, world):
        return [Shoot(tip.heading + 1)]


def persistent_world(persistence: int = 100, seed: int = 1, species: Species | None = None, **kwargs) -> World:
    """A world with a test species of the given persistence next to the straight vine."""
    species = species or Persistent(persistence)
    return World(seed=seed, catalog={species.id: species, VINE: CATALOG[VINE]}, **kwargs)


def obstacle(world: World, hex) -> None:
    """A root that will not grow for a very long time."""
    world.plant_seed(hex, VINE, "1/1000", "p2", direction=EAST)


def east_vine(length: int, speed="1", **world_kwargs) -> World:
    """A world with one vine grown ``length`` cells east from a root at (0, 0)."""
    world = World(seed=1, **world_kwargs)
    world.plant_seed((0, 0), VINE, speed, "p1", direction=EAST)
    while len(world.cells) < length + 1:
        world.step()
    return world


def steps(world: World, count: int) -> None:
    for _ in range(count):
        world.step()


def tips_at(world: World, hex) -> list[int]:
    """Sorted headings of the tips sitting on ``hex``."""
    return sorted(tip.heading for tip in world.tips.values() if tip.cell == hex)


def board(world: World) -> dict:
    return {hex: cell.to_dict() for hex, cell in world.cells.items()}
