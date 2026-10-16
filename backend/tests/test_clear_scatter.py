"""Clearing the board and scattering random seeds."""

from collections import Counter

import pytest

from plantastic.sim.species import CATALOG
from plantastic.sim.world import Changes, SimError, World

from .helpers import EAST, VINE, board, steps

PRESETS = {species.id for species in CATALOG.values() if not species.settings}


def in_region(hex, center, half_width, half_height) -> bool:
    dq, dr = hex[0] - center[0], hex[1] - center[1]
    return abs(dr) <= half_height and abs(dq + dr / 2) <= half_width


def region_hexes(center, half_width, half_height) -> list:
    reach = half_width + half_height + 2
    return [
        (center[0] + dq, center[1] + dr)
        for dq in range(-reach, reach + 1)
        for dr in range(-reach, reach + 1)
        if in_region((center[0] + dq, center[1] + dr), center, half_width, half_height)
    ]


def crowded_world() -> World:
    """Three plants, one cut (a stump) and one blocked (a waiting tip)."""
    world = World(seed=3)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    world.plant_seed((0, 6), "burst", "1", "p1", direction=EAST)
    world.plant_seed((4, 0), VINE, "1/1000", "p2", direction=EAST)
    steps(world, 8)
    world.cut((2, 6))  # the burst; the vine stays blocked behind the slow root
    steps(world, 2)
    assert any(cell.kind == "stump" for cell in world.cells.values())
    assert any(tip.blocked for tip in world.tips.values())
    return world


# -- clearing ----------------------------------------------------------------


def test_clear_removes_every_plant_cell_and_tip():
    world = crowded_world()
    changes = world.clear()

    assert changes.cleared
    assert not world.cells and not world.plants and not world.tips
    assert changes.added == changes.changed == changes.removed == []
    steps(world, 5)
    assert not world.cells


def test_clear_keeps_the_iteration_number():
    world = crowded_world()
    assert world.tick == 10
    world.clear()
    assert world.tick == 10
    world.step()
    assert world.tick == 11


def test_plants_after_a_clear_get_unused_ids_and_grow():
    world = crowded_world()
    old_ids = set(world.plants)
    world.clear()
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)

    (new_id,) = world.plants
    assert new_id not in old_ids
    steps(world, 4)
    assert set(world.cells) == {(n, 0) for n in range(5)}
    assert len(world.tips) == 1


def test_clearing_an_empty_board_changes_nothing():
    world = World(seed=3)
    rng_state = world.rng.getstate()
    changes = world.clear()

    assert changes.cleared
    assert not world.cells and world.tick == 0
    assert world.rng.getstate() == rng_state


def test_a_clear_inside_merged_changes_replays_onto_a_client_board():
    world = crowded_world()
    client = board(world)

    merged = Changes()
    merged.merge(world.step())
    merged.merge(world.clear())
    merged.merge(world.plant_seed((7, 7), VINE, "1", "p1", direction=EAST))
    merged.merge(world.step())
    merged.apply_to(client)

    assert merged.cleared
    assert client == board(world)
    assert set(client) == {(7, 7), (8, 7)}
    assert [plant["id"] for plant in merged.plants] == list(world.plants)


# -- scattering --------------------------------------------------------------


def test_scatter_plants_on_different_empty_hexes_inside_the_region():
    world = World(seed=5)
    changes = world.scatter(20, (3, -2), 12, 8, "alice")

    assert changes.scattered == {"asked": 20, "planted": 20}
    assert len(world.plants) == 20
    roots = [plant.root for plant in world.plants.values()]
    assert len(set(roots)) == 20
    assert all(in_region(root, (3, -2), 12, 8) for root in roots)
    assert len(world.tips) == 20
    for plant in world.plants.values():
        assert plant.owner == "alice"
        assert plant.settings is None
        assert plant.speed == CATALOG[plant.species_id].default_speed
    assert len(changes.plants) == 20 and len(changes.added) == 20


def test_region_is_a_rectangle_on_screen():
    # Fill a small region completely: the seeds land on exactly its hexes.
    world = World(seed=5)
    expected = set(region_hexes((0, 0), 2, 3))
    world.scatter(500, (0, 0), 2, 3, "p1")

    assert set(world.cells) == expected
    rows = Counter(r for _q, r in expected)
    assert set(rows) == set(range(-3, 4))
    # Even rows hold five hexes; odd rows are offset by half a hex and hold four.
    assert all(rows[r] == (5 if r % 2 == 0 else 4) for r in rows)
    assert all(abs(q + r / 2) <= 2 for q, r in expected)


def test_scatter_draws_only_species_without_settings_and_all_of_them():
    world = World(seed=5)
    world.scatter(400, (0, 0), 30, 30, "p1")
    species = Counter(plant.species_id for plant in world.plants.values())

    assert set(species) == PRESETS
    assert "custom" not in species
    assert len(PRESETS) == 7


def test_scatter_mix_is_not_balanced():
    repeats = 0
    for seed in range(40):
        world = World(seed=seed)
        world.scatter(7, (0, 0), 10, 10, "p1")
        species = [plant.species_id for plant in world.plants.values()]
        repeats += len(set(species)) < 7
    # Seven independent draws from seven species almost always repeat one.
    assert repeats >= 35


def test_scatter_avoids_occupied_hexes_and_leaves_them_alone():
    world = crowded_world()
    before = board(world)
    world.scatter(60, (2, 3), 8, 6, "p1")

    after = board(world)
    assert all(after[hex] == cell for hex, cell in before.items())
    assert len(after) == len(before) + 60
    assert all(in_region(hex, (2, 3), 8, 6) for hex in set(after) - set(before))


def test_scattered_plants_grow():
    world = World(seed=5)
    world.scatter(10, (0, 0), 40, 40, "p1")
    steps(world, 6)
    cells = Counter(cell.plant_id for cell in world.cells.values())
    assert all(cells[plant_id] > 1 for plant_id in world.plants)


def test_scatter_plants_as_many_as_fit_in_the_region():
    world = World(seed=5)
    hexes = region_hexes((0, 0), 2, 2)
    for hex in hexes[: len(hexes) - 12]:
        world.plant_seed(hex, VINE, "1/1000", "p2", direction=EAST)
    empty = set(hexes[len(hexes) - 12 :])

    changes = world.scatter(50, (0, 0), 2, 2, "p1")

    assert changes.scattered == {"asked": 50, "planted": 12}
    assert {plant.root for plant in world.plants.values() if plant.owner == "p1"} == empty


def test_scatter_in_a_full_region_plants_nothing():
    world = World(seed=5)
    world.scatter(500, (0, 0), 2, 2, "p1")
    before = (board(world), world.tips_snapshot())
    rng_state = world.rng.getstate()

    changes = world.scatter(10, (0, 0), 2, 2, "p1")

    assert changes.scattered == {"asked": 10, "planted": 0}
    assert changes.added == [] and changes.plants == []
    assert (board(world), world.tips_snapshot()) == before
    assert world.rng.getstate() == rng_state


def test_scatter_stops_at_the_board_limit():
    world = World(seed=5, max_cells=5)
    world.plant_seed((50, 50), VINE, "1/1000", "p2", direction=EAST)
    world.plant_seed((52, 50), VINE, "1/1000", "p2", direction=EAST)

    changes = world.scatter(20, (0, 0), 10, 10, "p1")

    assert changes.scattered == {"asked": 20, "planted": 3}
    assert len(world.cells) == 5


def test_single_hex_region():
    world = World(seed=5)
    changes = world.scatter(5, (9, -4), 0, 0, "p1")
    assert changes.scattered == {"asked": 5, "planted": 1}
    assert set(world.cells) == {(9, -4)}


def scattered(seed: int) -> list:
    world = World(seed=seed)
    world.scatter(30, (0, 0), 15, 10, "p1")
    return [(plant.root, plant.species_id, tip.heading) for plant, tip in zip(world.plants.values(), world.tips.values())]


def test_same_seed_scatters_identically_and_different_seeds_differ():
    assert scattered(8) == scattered(8)
    assert scattered(8) != scattered(9)


def test_scatter_with_a_persistence_gives_it_to_every_plant():
    world = World(seed=1)
    world.scatter(20, (0, 0), 10, 10, "p1", persistence=70)
    assert len(world.plants) == 20
    assert {plant.persistence for plant in world.plants.values()} == {70}


def test_scatter_without_a_persistence_uses_each_species_default():
    world = World(seed=1)
    world.scatter(60, (0, 0), 20, 20, "p1")
    assert all(plant.persistence == CATALOG[plant.species_id].persistence for plant in world.plants.values())
    assert len({plant.persistence for plant in world.plants.values()}) > 1


def test_scatter_with_a_bad_persistence_plants_nothing_and_draws_nothing():
    world = World(seed=1)
    rng_state = world.rng.getstate()
    with pytest.raises(SimError) as error:
        world.scatter(10, (0, 0), 5, 5, "p1", persistence=150)
    assert error.value.code == "bad_persistence"
    assert not world.plants and not world.cells
    assert world.rng.getstate() == rng_state
