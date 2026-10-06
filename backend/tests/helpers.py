from plantastic.sim.world import World

VINE = "straight-vine"
EAST, SOUTH_EAST, SOUTH_WEST, WEST, NORTH_WEST, NORTH_EAST = range(6)


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
