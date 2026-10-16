"""The four shared cut responses, exercised through the custom plant, which can use any of them."""

import pytest

from plantastic.sim.world import STUMP, SimError, World

from .helpers import EAST, NORTH_EAST, SOUTH_EAST, VINE, board, steps, tips_at

STRAIGHT = {
    "branch_chance": 0,
    "branch_min": 1,
    "branch_max": 1,
    "calm_min": 0,
    "calm_max": None,
    "turn_chance": 0,
    "persistence": 0,
    "cut_response": "fork",
}


def straight_plant(response: str, length: int = 6, seed: int = 1) -> World:
    """A custom plant that only grows straight, east from (0, 0), with the given cut response."""
    world = World(seed=seed)
    world.plant_seed((0, 0), "custom", "1", "p1", direction=EAST, settings={**STRAIGHT, "cut_response": response})
    steps(world, length)
    return world


def test_fork_matches_the_straight_vine():
    world = straight_plant("fork")
    world.cut((5, 0))
    assert tips_at(world, (3, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 2


def test_regrow_sprouts_one_tip_into_an_empty_neighbour():
    for seed in range(8):
        world = straight_plant("regrow", seed=seed)
        world.cut((5, 0))

        (tip,) = world.tips.values()
        assert tip.cell == (4, 0)
        # West is the vine and east is the stump, so four neighbours are empty.
        assert tip.heading in (1, 2, 4, 5)


def test_regrow_picks_different_directions_across_seeds():
    headings = set()
    for seed in range(40):
        world = straight_plant("regrow", seed=seed)
        world.cut((5, 0))
        headings.add(next(iter(world.tips.values())).heading)
    assert headings == {1, 2, 4, 5}


def test_regrow_with_no_room_sprouts_nothing():
    world = straight_plant("regrow")
    for hex in [(4, 1), (3, 1), (4, -1), (5, -1)]:  # the four empty neighbours of (4, 0)
        world.plant_seed(hex, VINE, "1/1000", "p2", direction=EAST)
    rng_state = world.rng.getstate()

    world.cut((5, 0))

    assert world.cells[(5, 0)].kind == STUMP
    assert not [tip for tip in world.tips.values() if tip.plant_id == 1]
    assert world.rng.getstate() == rng_state


def test_none_sprouts_nothing():
    world = straight_plant("none")
    world.cut((4, 0))

    assert world.cells[(4, 0)].kind == STUMP
    assert (5, 0) not in world.cells and (6, 0) not in world.cells
    assert not world.tips
    steps(world, 5)
    assert set(world.cells) == {(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}


def test_multiply_forks_from_both_cells_behind_the_stump():
    world = straight_plant("multiply")
    world.cut((5, 0))

    assert tips_at(world, (4, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert tips_at(world, (3, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 4


def test_multiply_next_to_the_root_forks_only_from_the_root():
    world = straight_plant("multiply")
    world.cut((1, 0))

    assert tips_at(world, (0, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 2


def test_multiply_two_cells_from_the_root_uses_the_root_as_the_second_cell():
    world = straight_plant("multiply")
    world.cut((2, 0))

    assert tips_at(world, (1, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert tips_at(world, (0, 0)) == [SOUTH_EAST, NORTH_EAST]


def test_each_custom_plant_uses_its_chosen_response():
    tips_after_cut = {}
    for response in ("fork", "regrow", "none", "multiply"):
        world = straight_plant(response)
        world.cut((5, 0))
        tips_after_cut[response] = sorted((tip.cell, tip.heading) for tip in world.tips.values())

    assert [cell for cell, _ in tips_after_cut["fork"]] == [(3, 0), (3, 0)]
    assert [cell for cell, _ in tips_after_cut["regrow"]] == [(4, 0)]
    assert tips_after_cut["none"] == []
    assert [cell for cell, _ in tips_after_cut["multiply"]] == [(3, 0), (3, 0), (4, 0), (4, 0)]


# -- planting with settings ------------------------------------------------


def test_settings_are_stored_on_the_plant():
    world = World(seed=1)
    settings = {**STRAIGHT, "branch_chance": 35, "calm_max": 9}
    world.plant_seed((0, 0), "custom", "1", "p1", settings=settings)

    assert world.plants[1].settings == settings
    assert world.plants[1].settings is not settings
    assert world.plants[1].to_dict() == {"id": 1, "species": "custom", "speed": "1", "settings": settings, "persistence": 0}


@pytest.mark.parametrize(
    "change",
    [
        {"branch_chance": 150},
        {"branch_chance": -1},
        {"turn_chance": 101},
        {"persistence": 101},
        {"persistence": -1},
        {"persistence": 50.5},
        {"branch_max": 5},
        {"branch_min": 0},
        {"calm_min": -1},
        {"calm_min": 1001},
        {"calm_max": 1001},
        {"cut_response": "explode"},
        {"cut_response": 3},
        {"branch_min": 3, "branch_max": 2},
        {"calm_min": 5, "calm_max": 4},
        {"branch_chance": 10.5},
        {"branch_chance": "10"},
        {"branch_chance": True},
        {"branch_chance": None},
        {"calm_min": None},
        {"extra": 1},
    ],
)
def test_invalid_custom_settings_are_rejected(change):
    world = World(seed=1)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), "custom", "1", "p1", settings={**STRAIGHT, **change})
    assert error.value.code == "bad_settings"
    assert not world.cells and not world.plants and not world.tips


@pytest.mark.parametrize("missing", list(STRAIGHT))
def test_missing_custom_setting_is_rejected(missing):
    world = World(seed=1)
    settings = {key: value for key, value in STRAIGHT.items() if key != missing}
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), "custom", "1", "p1", settings=settings)
    assert error.value.code == "bad_settings"
    assert not world.cells


@pytest.mark.parametrize("settings", [None, "fork", [], 5])
def test_custom_seed_without_settings_is_rejected(settings):
    world = World(seed=1)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), "custom", "1", "p1", settings=settings)
    assert error.value.code == "bad_settings"
    assert not world.cells


def test_settings_for_a_species_without_any_are_rejected():
    world = World(seed=1)
    before = board(world)
    for settings in ({}, STRAIGHT):
        with pytest.raises(SimError) as error:
            world.plant_seed((0, 0), VINE, "1", "p1", settings=settings)
        assert error.value.code == "bad_settings"
    assert board(world) == before and not world.plants


@pytest.mark.parametrize(
    "edge",
    [
        {"branch_chance": 0, "turn_chance": 0},
        {"branch_chance": 100, "turn_chance": 100},
        {"persistence": 0},
        {"persistence": 100},
        {"branch_min": 4, "branch_max": 4},
        {"calm_min": 0, "calm_max": 0},
        {"calm_min": 1000, "calm_max": 1000},
        {"calm_min": 7, "calm_max": None},
    ],
)
def test_settings_at_the_edges_of_their_ranges_are_accepted(edge):
    world = World(seed=1)
    world.plant_seed((0, 0), "custom", "1", "p1", settings={**STRAIGHT, **edge})
    assert world.plants[1].settings == {**STRAIGHT, **edge}
