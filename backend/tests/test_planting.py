from fractions import Fraction

import pytest

from plantastic.sim.world import ROOT, SimError, World, parse_speed

from .helpers import EAST, VINE, board


def test_seed_creates_root_tip_and_owner():
    world = World(seed=7)
    world.plant_seed((2, -1), VINE, "1", "alice")

    assert world.cells[(2, -1)].kind == ROOT
    (plant,) = world.plants.values()
    assert plant.owner == "alice"
    (tip,) = world.tips.values()
    assert tip.cell == (2, -1)
    assert tip.heading in range(6)
    assert tip.progress == 0


def test_given_direction_is_used():
    world = World(seed=7)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=4)
    (tip,) = world.tips.values()
    assert tip.heading == 4


def test_hex_holds_at_most_one_cell():
    world = World(seed=7)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    before = board(world)

    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), VINE, "1", "p2")

    assert error.value.code == "occupied"
    assert board(world) == before
    assert len(world.plants) == 1


def test_unknown_species_is_rejected():
    world = World(seed=7)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), "triffid", "1", "p1")
    assert error.value.code == "unknown_species"
    assert not world.cells


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0.25", Fraction(1, 4)),
        ("1/4", Fraction(1, 4)),
        ("2", Fraction(2)),
        (" 0.3 ", Fraction(3, 10)),
        ("10", Fraction(10)),
    ],
)
def test_speed_is_parsed_exactly(text, expected):
    assert parse_speed(text) == expected


@pytest.mark.parametrize(
    "bad", ["0", "-1", "abc", "", "10.5", "1/0", "nan", "inf", None, True, float("nan")]
)
def test_bad_speed_is_rejected(bad):
    world = World(seed=7)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), VINE, bad, "p1")
    assert error.value.code == "bad_speed"
    assert not world.cells
    assert not world.plants
