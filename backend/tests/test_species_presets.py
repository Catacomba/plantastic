"""Growth patterns and cut responses of the six preset species."""

from plantastic.sim.hex import DIRECTIONS, direction_between, neighbor, turn_left, turn_right
from plantastic.sim.species import CATALOG, Burst, Hydra, Wanderer, Zigzag
from plantastic.sim.world import ROOT, SEGMENT, STUMP, World

from .helpers import EAST, NORTH_EAST, NORTH_WEST, SOUTH_EAST, SOUTH_WEST, WEST, board, steps, tips_at

PRESETS = ["zigzag", "spiral", "fern", "wanderer", "hydra", "burst"]


def grown(species: str, iterations: int, direction: int = EAST, seed: int = 1, speed: str = "1") -> World:
    world = World(seed=seed)
    world.plant_seed((0, 0), species, speed, "p1", direction=direction)
    steps(world, iterations)
    return world


def path_from_root(world: World, plant_id: int = 1) -> list:
    """The cells of an unbranched plant, in order from the root."""
    cells = [cell for cell in world.cells.values() if cell.plant_id == plant_id]
    path = [next(cell.hex for cell in cells if cell.kind == ROOT)]
    while True:
        following = [cell.hex for cell in cells if cell.parent == path[-1]]
        if not following:
            return path
        assert len(following) == 1, "the plant has branched"
        path.append(following[0])


def headings(path: list) -> list:
    return [direction_between(a, b) for a, b in zip(path, path[1:])]


def walk(start, moves: list) -> list:
    """The hexes reached from ``start`` by a list of (heading, count) moves."""
    cells, current = [], start
    for heading, count in moves:
        for _ in range(count):
            current = neighbor(current, heading)
            cells.append(current)
    return cells


def test_catalog_holds_exactly_the_eight_species():
    assert list(CATALOG) == ["straight-vine", *PRESETS, "custom"]
    assert all(CATALOG[species].settings == () for species in ["straight-vine", *PRESETS])
    assert [setting.id for setting in CATALOG["custom"].settings] == [
        "branch_chance",
        "branch_min",
        "branch_max",
        "calm_min",
        "calm_max",
        "turn_chance",
        "persistence",
        "cut_response",
    ]


def test_each_preset_has_its_persistence():
    assert {species.id: species.persistence for species in CATALOG.values() if not species.settings} == {
        "straight-vine": 0,
        "zigzag": 30,
        "spiral": 30,
        "fern": 0,
        "wanderer": 60,
        "hydra": 80,
        "burst": 30,
    }
    world = World(seed=1)
    world.plant_seed((0, 0), "hydra", "1", "p1")
    assert CATALOG["hydra"].persistence_of(world.plants[1]) == 80


def test_settings_descriptions_name_kind_range_and_default():
    descriptions = {setting.id: setting.describe() for setting in CATALOG["custom"].settings}
    assert descriptions["branch_chance"] == {
        "id": "branch_chance",
        "label": "Branch chance %",
        "kind": "percent",
        "default": 10,
        "min": 0,
        "max": 100,
    }
    assert descriptions["persistence"] == {
        "id": "persistence",
        "label": "Persistence %",
        "kind": "percent",
        "default": 50,
        "min": 0,
        "max": 100,
    }
    assert descriptions["calm_max"]["kind"] == "optional_int" and descriptions["calm_max"]["default"] is None
    assert [choice["id"] for choice in descriptions["cut_response"]["choices"]] == [
        "fork",
        "regrow",
        "none",
        "multiply",
    ]
    defaults = {id: description["default"] for id, description in descriptions.items()}
    assert CATALOG["custom"].validate(defaults) == defaults


# -- zigzag ------------------------------------------------------------------


def test_zigzag_travels_in_a_wavy_line():
    world = grown("zigzag", 6)
    assert headings(path_from_root(world)) == [EAST, SOUTH_EAST, EAST, SOUTH_EAST, EAST, SOUTH_EAST]
    assert len(world.tips) == 1


def test_zigzag_cut_mirrors_the_new_growth():
    world = grown("zigzag", 6)
    path = path_from_root(world)
    stump, behind = path[4], path[3]
    world.cut(stump)

    to_stump = direction_between(behind, stump)
    left = turn_left(to_stump)
    (tip,) = world.tips.values()
    assert tip.cell == behind and tip.heading == left
    assert world.cells[stump].kind == STUMP

    steps(world, 4)
    new_cells = walk(behind, [(left, 1), (turn_left(left), 1), (left, 1), (turn_left(left), 1)])
    assert all(world.cells[hex].kind == SEGMENT for hex in new_cells)


def test_zigzag_second_cut_flips_back_to_the_right():
    world = grown("zigzag", 6)
    path = path_from_root(world)
    world.cut(path[4])
    steps(world, 4)
    regrowth = [cell.hex for cell in world.cells.values() if cell.hex not in path]
    last = max(regrowth, key=lambda hex: len(ancestors(world, hex)))
    behind = world.cells[last].parent
    world.cut(last)

    new_tip = next(tip for tip in world.tips.values() if tip.cell == behind)
    assert new_tip.heading == turn_right(direction_between(behind, last))
    assert new_tip.state["hand"] == 1


def ancestors(world: World, hex) -> list:
    chain = []
    while world.cells[hex].parent is not None:
        hex = world.cells[hex].parent
        chain.append(hex)
    return chain


# -- spiral ------------------------------------------------------------------


def test_spiral_run_lengths():
    world = grown("spiral", 12)
    expected = walk((0, 0), [(EAST, 1), (SOUTH_EAST, 1), (SOUTH_WEST, 2), (WEST, 2), (NORTH_WEST, 3), (NORTH_EAST, 3)])
    assert path_from_root(world)[1:] == expected


def test_spiral_never_crosses_itself():
    for direction in (EAST, NORTH_WEST):
        world = World(seed=1)
        world.plant_seed((0, 0), "spiral", "1", "p1", direction=direction)
        for _ in range(1000):
            world.step()
            assert not any(tip.blocked for tip in world.tips.values())
        assert len(world.cells) == 1001


def test_spiral_cut_reverses_the_winding():
    world = grown("spiral", 12)
    path = path_from_root(world)
    stump, behind = path[9], path[8]
    world.cut(stump)

    start = turn_left(direction_between(behind, stump))
    (tip,) = world.tips.values()
    assert tip.cell == behind and tip.heading == start

    steps(world, 6)
    moves = [(start, 1)]
    for run in (1, 2, 2):
        moves.append((turn_left(moves[-1][0]), run))
    assert all(hex in world.cells for hex in walk(behind, moves))


# -- fern --------------------------------------------------------------------


def test_fern_stem_and_side_branches():
    world = grown("fern", 13)
    stem = walk((0, 0), [(EAST, 13)])
    assert all(world.cells[hex].kind == SEGMENT for hex in stem)

    left_3 = walk((3, 0), [(NORTH_EAST, 3)])
    right_6 = walk((6, 0), [(SOUTH_EAST, 3)])
    left_9 = walk((9, 0), [(NORTH_EAST, 3)])
    assert set(world.cells) == {(0, 0), *stem, *left_3, *right_6, *left_9}

    # The stem's tip, and a new side tip on cell 12 that has not grown yet.
    assert tips_at(world, (13, 0)) == [EAST]
    assert tips_at(world, (12, 0)) == [SOUTH_EAST]
    assert len(world.tips) == 2


def test_fern_side_branch_loses_its_tip_on_its_third_cell():
    world = grown("fern", 6)  # the first side branch sprouts on iteration 4 and grows on 5, 6, 7
    assert tips_at(world, (5, -2)) == [NORTH_EAST]
    world.step()

    assert (6, -3) in world.cells
    assert tips_at(world, (6, -3)) == []
    steps(world, 10)
    assert (7, -4) not in world.cells
    assert not [cell for cell in world.cells.values() if cell.parent == (6, -3)]


def test_fern_cut_is_final_but_side_branches_finish():
    world = grown("fern", 11)  # the branch on cell 9 has grown one of its three cells
    assert (10, -1) in world.cells and (11, -2) not in world.cells
    world.cut((10, 0))

    assert world.cells[(10, 0)].kind == STUMP
    assert [tip.cell for tip in world.tips.values()] == [(10, -1)]
    steps(world, 10)

    assert {(10, -1), (11, -2), (12, -3)} <= set(world.cells)
    assert not world.tips
    assert (11, 0) not in world.cells


# -- wanderer ----------------------------------------------------------------


class SettledWanderer(Wanderer):
    """A wanderer that never takes another path, so every step it takes is one it chose."""

    persistence = 0


def wander(seed: int, wanted: int = 500, settled: bool = False) -> list:
    """The headings of a wanderer's first ``wanted`` steps, or fewer if it stopped.

    A settled wanderer never detours, which isolates the wanderer's own turning rule.
    """
    world = World(seed=seed, catalog={"wanderer": SettledWanderer()} if settled else None)
    world.plant_seed((0, 0), "wanderer", "1", "p1", direction=EAST)
    for _ in range(wanted):
        world.step()
        if any(tip.blocked for tip in world.tips.values()):
            break
    return headings(path_from_root(world))


def test_wanderer_makes_only_gentle_turns_about_a_fifth_of_the_time():
    changes = []
    for seed in range(60):
        taken = wander(seed, 300, settled=True)
        changes += [(b - a) % 6 for a, b in zip(taken, taken[1:])]

    assert len(changes) > 3000
    assert set(changes) == {0, 1, 5}  # straight, right, left
    turns = sum(1 for change in changes if change)
    assert 0.15 <= turns / len(changes) <= 0.25
    rights = sum(1 for change in changes if change == 1)
    assert 0.4 <= rights / turns <= 0.6


def test_wanderer_detours_add_at_most_one_more_turn():
    changes = []
    for seed in range(60):
        taken = wander(seed, 300)
        changes += [(b - a) % 6 for a, b in zip(taken, taken[1:])]

    # A detour turns 60 degrees from where the wanderer meant to go, which may
    # itself be a turn; it never doubles back.
    assert 3 not in changes
    assert {2, 4} & set(changes)


def test_wanderer_waits_when_it_runs_into_itself():
    world = World(seed=0)
    world.plant_seed((0, 0), "wanderer", "1", "p1", direction=EAST)
    for _ in range(2000):
        world.step()
        if any(tip.blocked for tip in world.tips.values()):
            break
    (tip,) = world.tips.values()
    assert tip.blocked  # it lost its roll, or had no free side to turn to
    assert world.cells[neighbor(tip.cell, tip.heading)].plant_id == 1

    size = len(world.cells)
    heading = tip.heading
    steps(world, 20)
    assert len(world.cells) == size and tip.heading == heading


def test_wanderer_same_seed_same_path_and_different_seed_different_path():
    assert wander(3, 200) == wander(3, 200)
    assert wander(3, 200) != wander(4, 200)


def test_wanderer_never_branches_and_regrows_when_cut():
    world = grown("wanderer", 30, seed=5)
    path = path_from_root(world)
    assert len(world.tips) == 1
    stump, behind = path[6], path[5]
    world.cut(stump)

    (tip,) = world.tips.values()
    assert tip.cell == behind
    assert neighbor(behind, tip.heading) not in world.cells


# -- hydra -------------------------------------------------------------------


def test_hydra_grows_straight():
    world = grown("hydra", 5)
    assert path_from_root(world) == [(n, 0) for n in range(6)]
    assert tips_at(world, (5, 0)) == [EAST]


def test_hydra_cut_multiplies():
    world = grown("hydra", 6)
    world.cut((5, 0))

    assert tips_at(world, (4, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert tips_at(world, (3, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 4
    steps(world, 3)
    assert not any(tip.blocked for tip in world.tips.values())


# -- burst -------------------------------------------------------------------


def test_burst_first_fan():
    world = grown("burst", 6)
    stem = walk((0, 0), [(EAST, 6)])
    assert set(world.cells) == {(0, 0), *stem, (5, -1), (4, 1)}
    assert world.cells[(5, -1)].parent == (4, 0) and world.cells[(4, 1)].parent == (4, 0)
    assert len(world.tips) == 3


def test_burst_fans_repeat():
    world = grown("burst", 8)
    assert len(world.tips) == 3
    world.step()
    assert len(world.tips) == 5  # the stem fans again on reaching its eighth cell
    world.step()
    assert len(world.tips) == 9  # and so do both arms of the first fan
    assert not any(tip.blocked for tip in world.tips.values())


def test_burst_cut_forks_like_the_vine():
    world = grown("burst", 4)
    world.cut((4, 0))
    assert tips_at(world, (2, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 2


# -- all presets -------------------------------------------------------------


def run_all(seed: int) -> list:
    world = World(seed=seed)
    history = []
    for index, species in enumerate(PRESETS):
        world.plant_seed((index * 40, 0), species, ["1", "0.5", "2"][index % 3], "p1")
    for tick in range(36):
        if tick in (10, 20, 30):
            # Cut one cell of every plant, chosen in a stable order.
            for plant_id in list(world.plants):
                segments = sorted(
                    cell.hex for cell in world.cells.values() if cell.plant_id == plant_id and cell.kind == SEGMENT
                )
                if segments:
                    world.cut(segments[len(segments) // 2])
        world.step()
        history.append((board(world), world.tips_snapshot()))
    return history


def test_presets_replay_identically_from_the_same_seed():
    first = run_all(21)
    assert first == run_all(21)
    assert first != run_all(22)


def test_every_direction_table_entry_is_used():
    # A guard for the helpers above: walking all six directions returns to the start.
    assert walk((0, 0), [(d, 1) for d in range(6)])[-1] == (0, 0)
    assert len(DIRECTIONS) == 6


# -- after taking another path -----------------------------------------------


def always_detouring(species_class, seed: int = 1) -> World:
    """A world where the given preset always takes another path when it can."""
    species = type(f"Persistent{species_class.__name__}", (species_class,), {"persistence": 100})()
    return World(seed=seed, catalog={species.id: species, "straight-vine": CATALOG["straight-vine"]})


def obstacle(world: World, hex) -> None:
    world.plant_seed(hex, "straight-vine", "1/1000", "p2", direction=EAST)


def test_zigzag_sidesteps_and_keeps_its_line():
    world = always_detouring(Zigzag)
    world.plant_seed((0, 0), "zigzag", "1", "p1", direction=EAST)
    obstacle(world, (2, 1))  # in the way of the third step, east from (1, 1)
    obstacle(world, (2, 0))  # leaves only south-east
    steps(world, 9)

    taken = headings(path_from_root(world))
    assert taken[:3] == [EAST, SOUTH_EAST, SOUTH_EAST]  # the third step is the detour
    assert taken[3:] == [SOUTH_EAST, EAST, SOUTH_EAST, EAST, SOUTH_EAST, EAST]


def test_burst_arm_turns_and_still_fans_after_four_cells():
    world = always_detouring(Burst)
    world.plant_seed((0, 0), "burst", "1", "p1", direction=EAST)
    obstacle(world, (3, 0))
    obstacle(world, (3, -1))  # leaves only south-east from (2, 0)
    steps(world, 6)

    # (1, 0), (2, 0), then south-east (2, 1), (2, 2): the fourth cell fans.
    assert {(2, 1), (2, 2), (2, 3), (2, 4)} <= set(world.cells)
    assert tips_at(world, (2, 4)) == [SOUTH_EAST]
    assert world.cells[(3, 2)].parent == (2, 2)  # forward-left of south-east is east
    assert world.cells[(1, 3)].parent == (2, 2)  # forward-right is south-west


def test_hydra_keeps_its_new_direction():
    world = always_detouring(Hydra)
    world.plant_seed((0, 0), "hydra", "1", "p1", direction=EAST)
    obstacle(world, (2, 0))
    obstacle(world, (2, -1))
    steps(world, 6)

    assert headings(path_from_root(world)) == [EAST] + [SOUTH_EAST] * 5


def test_straight_vine_and_fern_never_take_another_path():
    for species in ("straight-vine", "fern"):
        world = World(seed=1)
        world.plant_seed((0, 0), species, "1", "p1", direction=EAST)
        obstacle(world, (2, 0))
        steps(world, 2)
        rng_state = world.rng.getstate()
        steps(world, 20)

        stem = next(tip for tip in world.tips.values() if tip.plant_id == 1 and tip.cell == (1, 0))
        assert stem.blocked and stem.heading == EAST
        assert world.rng.getstate() == rng_state
