from fractions import Fraction

from plantastic.sim.species import CATALOG
from plantastic.sim.world import ROOT, SEGMENT, World

from .helpers import NORTH_WEST, VINE


def test_catalog_lists_the_straight_vine():
    vine = CATALOG[VINE]
    assert vine.id == VINE
    assert vine.name == "Straight vine"
    assert vine.default_speed == Fraction(1)


def test_catalog_lookup_rejects_unknown_id():
    assert CATALOG.get("triffid") is None


def test_straight_vine_grows_in_a_straight_line():
    world = World(seed=3)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=NORTH_WEST)
    for _ in range(5):
        world.step()

    assert world.cells[(0, 0)].kind == ROOT
    line = [(0, -n) for n in range(1, 6)]
    assert set(world.cells) == {(0, 0), *line}
    assert all(world.cells[hex].kind == SEGMENT for hex in line)
    (tip,) = world.tips.values()
    assert tip.cell == (0, -5)
    assert tip.heading == NORTH_WEST
