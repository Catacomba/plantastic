import pytest

from plantastic.sim.hex import neighbor
from plantastic.sim.world import SEGMENT, SimError, World

from .helpers import (
    EAST,
    NORTH_EAST,
    NORTH_WEST,
    SOUTH_EAST,
    SOUTH_WEST,
    VINE,
    WEST,
    Circler,
    board,
    east_vine,
    obstacle,
    persistent_world,
    steps,
)


def growth_ticks(speed: str, iterations: int) -> list[int]:
    """The iterations at which an unobstructed plant gained a hex."""
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, speed, "p1", direction=EAST)
    ticks = []
    for _ in range(iterations):
        before = len(world.cells)
        world.step()
        ticks.extend([world.tick] * (len(world.cells) - before))
    return ticks


def test_fractional_speed():
    assert growth_ticks("0.25", 8) == [4, 8]


def test_speed_above_one():
    assert growth_ticks("2", 3) == [1, 1, 2, 2, 3, 3]


def test_remainder_carries_over():
    assert growth_ticks("0.3", 10) == [4, 7, 10]


def blocked_vine() -> tuple[World, int]:
    """A vine heading east that is stopped by another plant's root at (3, 0)."""
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    world.plant_seed((3, 0), VINE, "1/1000", "p1", direction=EAST)
    (tip_id,) = [tip.id for tip in world.tips.values() if tip.plant_id == 1]
    return world, tip_id


def test_blocked_tip_waits_without_turning():
    world, tip_id = blocked_vine()
    steps(world, 22)

    tip = world.tips[tip_id]
    assert tip.cell == (2, 0)
    assert tip.heading == EAST
    assert tip.blocked
    assert tip.progress == 1
    assert (2, 1) not in world.cells and (3, -1) not in world.cells


def test_blocked_tip_resumes_without_a_burst():
    world, tip_id = blocked_vine()
    steps(world, 22)
    world.cut((3, 0))  # cutting the root removes the obstacle

    world.step()
    assert world.tips[tip_id].cell == (3, 0)
    assert not world.tips[tip_id].blocked
    world.step()
    assert world.tips[tip_id].cell == (4, 0)


def test_fast_blocked_tip_does_not_bank_progress():
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, "2", "p1", direction=EAST)
    world.plant_seed((3, 0), VINE, "1/1000", "p1", direction=EAST)
    steps(world, 10)
    world.cut((3, 0))
    world.step()
    (tip,) = world.tips.values()
    assert tip.cell == (3, 0)


@pytest.mark.parametrize("first, second", [((0, 0), (2, 0)), ((2, 0), (0, 0))])
def test_earliest_plant_wins_a_contested_hex(first, second):
    headings = {(0, 0): EAST, (2, 0): WEST}
    world = World(seed=1)
    world.plant_seed(first, VINE, "1", "p1", direction=headings[first])
    world.plant_seed(second, VINE, "1", "p2", direction=headings[second])
    world.step()

    assert world.cells[(1, 0)].plant_id == 1
    assert world.cells[(1, 0)].parent == first
    loser = next(tip for tip in world.tips.values() if tip.plant_id == 2)
    assert loser.cell == second
    assert loser.blocked


def test_growth_stops_at_the_board_limit():
    world = World(seed=1, max_cells=5)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    reports = [world.step().full for _ in range(8)]

    assert len(world.cells) == 5
    assert reports == [False, False, False, False, True, True, True, True]


def test_planting_is_rejected_on_a_full_board():
    world = east_vine(4, max_cells=5)
    before = board(world)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 5), VINE, "1", "p1")
    assert error.value.code == "board_full"
    assert board(world) == before


def test_growth_resumes_after_a_cut_frees_space():
    world = east_vine(4, max_cells=5)
    assert world.step().full
    world.cut((2, 0))  # removes (3, 0) and (4, 0)
    assert len(world.cells) == 3

    world.step()
    assert len(world.cells) == 5


def run_script(seed: int) -> list:
    """A fixed session of plantings and cuts; returns the state after every iteration."""
    world = World(seed=seed)
    history = []
    for tick in range(40):
        if tick == 0:
            for index in range(6):
                speed = ["1", "0.3", "2"][index % 3]
                world.plant_seed((index * 7, -index * 3), VINE, speed, "p1")
        if tick in (9, 17, 26):
            # Cut a living non-root cell chosen in a stable order.
            target = min(hex for hex, cell in world.cells.items() if cell.kind == "segment")
            world.cut(target)
        world.step()
        history.append((board(world), world.tips_snapshot()))
    return history


def test_same_seed_gives_identical_boards_every_iteration():
    assert run_script(11) == run_script(11)


def test_different_seeds_give_different_seed_directions():
    def directions(seed):
        world = World(seed=seed)
        for index in range(8):
            world.plant_seed((index * 5, 0), VINE, "1", "p1")
        return [tip.heading for tip in world.tips.values()]

    assert directions(11) == directions(11)
    assert directions(11) != directions(12)


# -- tip visits ---------------------------------------------------------------


def visits_per_iteration(speed: str, iterations: int) -> list[int]:
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, speed, "p1", direction=EAST)
    return [world.step().visits for _ in range(iterations)]


def test_one_unobstructed_tip_is_one_visit_per_iteration():
    assert visits_per_iteration("1", 4) == [1, 1, 1, 1]


def test_fast_tip_is_visited_once_for_each_hex_entered():
    assert visits_per_iteration("2", 3) == [2, 2, 2]


def test_tip_that_is_not_due_is_not_visited():
    assert visits_per_iteration("0.25", 8) == [0, 0, 0, 1, 0, 0, 0, 1]


def test_waiting_tip_is_visited_every_iteration():
    world, _ = blocked_vine()
    world.skip_stuck = False  # otherwise the stuck vine sleeps and is not visited
    steps(world, 5)
    cells = len(world.cells)
    # Only the blocked vine is due; the slow obstacle is not.
    assert [world.step().visits for _ in range(4)] == [1, 1, 1, 1]
    assert len(world.cells) == cells


def test_merged_changes_sum_their_visits():
    from plantastic.sim.world import Changes

    world = World(seed=1)
    world.plant_seed((0, 0), VINE, "2", "p1", direction=EAST)
    world.plant_seed((0, 9), VINE, "1", "p1", direction=EAST)
    merged = Changes()
    for _ in range(5):
        merged.merge(world.step())
    assert merged.visits == 15


def test_same_seed_worlds_report_the_same_visits():
    def visits(seed):
        world = World(seed=seed)
        for index in range(4):
            world.plant_seed((index * 30, 0), ["burst", "wanderer", "fern", "zigzag"][index], "1", "p1")
        return [world.step().visits for _ in range(30)]

    assert visits(4) == visits(4)
    assert sum(visits(4)) > 60


# -- taking another path --------------------------------------------------------


def blocked_ahead(persistence: int = 100, seed: int = 1, **kwargs) -> World:
    """A test plant heading east from (0, 0) whose second hex, (2, 0), is taken."""
    world = persistent_world(persistence, seed=seed, **kwargs)
    world.plant_seed((0, 0), "persistent", "1", "p1", direction=EAST)
    obstacle(world, (2, 0))
    return world


def own_tip(world: World):
    return next(tip for tip in world.tips.values() if tip.plant_id == 1)


def test_persistent_tip_turns_into_the_only_empty_side_at_once():
    world = blocked_ahead()
    obstacle(world, (2, -1))  # north-east of (1, 0)
    steps(world, 2)

    tip = own_tip(world)
    assert tip.cell == (1, 1) and tip.heading == SOUTH_EAST
    assert not tip.blocked
    assert world.cells[(1, 1)].parent == (1, 0)
    world.step()
    assert tip.cell == (1, 2)  # a straight grower carries on in its new direction


def test_detours_go_to_either_side():
    sides = set()
    for seed in range(40):
        world = blocked_ahead(seed=seed)
        steps(world, 2)
        sides.add(own_tip(world).heading)
    assert sides == {NORTH_EAST, SOUTH_EAST}


def test_no_empty_side_waits_without_drawing():
    world = blocked_ahead()
    for hex in ((2, -1), (1, 1), (1, -1), (0, 1)):  # every 60 and 120 degree turn from (1, 0)
        obstacle(world, hex)
    world.step()
    rng_state = world.rng.getstate()

    steps(world, 20)
    tip = own_tip(world)
    assert tip.cell == (1, 0) and tip.heading == EAST and tip.blocked
    assert world.rng.getstate() == rng_state


def test_only_a_sharp_turn_free_is_taken():
    world = blocked_ahead()
    for hex in ((2, -1), (1, 1), (0, 1)):  # both 60 degree turns, and the south-west sharp turn
        obstacle(world, hex)
    steps(world, 2)

    tip = own_tip(world)
    assert tip.cell == (1, -1) and tip.heading == NORTH_WEST
    assert not tip.blocked
    assert world.cells[(1, -1)].parent == (1, 0)


def test_sharp_detours_go_to_either_side():
    sides = set()
    for seed in range(40):
        world = blocked_ahead(seed=seed)
        obstacle(world, (2, -1))
        obstacle(world, (1, 1))
        steps(world, 2)
        sides.add(own_tip(world).heading)
    assert sides == {NORTH_WEST, SOUTH_WEST}


def test_a_gentle_turn_is_preferred_to_sharp_ones():
    for seed in range(40):
        world = blocked_ahead(seed=seed)
        obstacle(world, (2, -1))  # north-east taken; south-east and both sharp turns free
        steps(world, 2)
        assert own_tip(world).heading == SOUTH_EAST


def test_full_board_waits_without_drawing_and_rolls_once_there_is_room():
    world = blocked_ahead(max_cells=3)
    world.step()  # enters (1, 0); the board is now full
    rng_state = world.rng.getstate()

    steps(world, 10)
    tip = own_tip(world)
    assert tip.cell == (1, 0) and tip.blocked
    assert world.rng.getstate() == rng_state

    world.max_cells = 4
    world.step()
    assert tip.cell in {(2, -1), (1, 1)}
    assert world.rng.getstate() != rng_state


def test_own_cells_are_an_obstacle_too():
    world = persistent_world(species=Circler(100))
    world.plant_seed((0, 0), "circler", "1", "p1", direction=NORTH_EAST)
    steps(world, 5)  # a ring around (0, 1), ending at (-1, 1) heading back to the root
    assert len(world.cells) == 6

    world.step()
    (tip,) = world.tips.values()
    assert not tip.blocked
    assert len(world.cells) == 7
    assert tip.cell in {(-1, 0), (0, 1)}


def test_the_loser_of_a_contested_hex_takes_another_path():
    world = persistent_world(100)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    world.plant_seed((2, 0), "persistent", "1", "p2", direction=WEST)
    world.step()

    assert world.cells[(1, 0)].plant_id == 1
    loser = next(tip for tip in world.tips.values() if tip.plant_id == 2)
    assert loser.cell in {(1, 1), (2, -1)}
    assert not loser.blocked


def crowded_script(seed: int) -> list:
    """Persistent presets planted close together; returns the state after every iteration."""
    world = World(seed=seed)
    history = []
    species = ["hydra", "wanderer", "burst", "zigzag", "spiral"]
    for index in range(10):
        world.plant_seed((index % 5 * 3, index // 5 * 3), species[index % 5], "1", "p1")
    for _ in range(60):
        world.step()
        history.append((board(world), world.tips_snapshot()))
    return history


def test_same_seed_gives_identical_boards_with_detours():
    assert crowded_script(5) == crowded_script(5)
    assert crowded_script(5) != crowded_script(6)


# -- persistence chosen at planting ---------------------------------------------


def test_a_straight_vine_planted_with_full_persistence_takes_another_path():
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST, persistence=100)
    world.plant_seed((2, 0), VINE, "1/1000", "p2", direction=EAST)
    assert world.plants[1].persistence == 100
    steps(world, 2)

    tip = next(tip for tip in world.tips.values() if tip.plant_id == 1)
    assert not tip.blocked and tip.cell in {(2, -1), (1, 1)}


def test_without_a_persistence_the_species_default_is_used():
    world = World(seed=1)
    world.plant_seed((0, 0), "hydra", "1", "p1")
    world.plant_seed((0, 9), VINE, "1", "p1")
    assert world.plants[1].persistence == 80
    assert world.plants[2].persistence == 0
    assert world.plants[1].to_dict()["persistence"] == 80


def test_a_custom_plant_takes_the_override_and_keeps_its_setting():
    from .test_cut_responses import STRAIGHT

    world = World(seed=1)
    world.plant_seed((0, 0), "custom", "1", "p1", settings={**STRAIGHT, "persistence": 0}, persistence=100)
    world.plant_seed((0, 9), "custom", "1", "p1", settings={**STRAIGHT, "persistence": 35})
    assert world.plants[1].persistence == 100
    assert world.plants[1].settings["persistence"] == 0
    assert world.plants[2].persistence == 35


@pytest.mark.parametrize("persistence", [101, -1, 50.5, True, "50"])
def test_invalid_persistence_is_rejected(persistence):
    world = World(seed=1)
    before = board(world)
    with pytest.raises(SimError) as error:
        world.plant_seed((0, 0), VINE, "1", "p1", persistence=persistence)
    assert error.value.code == "bad_persistence"
    assert board(world) == before and not world.plants


@pytest.mark.parametrize("persistence", [0, 100])
def test_persistence_at_the_edges_is_accepted(persistence):
    world = World(seed=1)
    world.plant_seed((0, 0), "hydra", "1", "p1", persistence=persistence)
    assert world.plants[1].persistence == persistence


# -- stuck tips sleep -----------------------------------------------------------


def test_stuck_tip_falls_asleep_and_is_no_longer_visited():
    world, tip_id = blocked_vine()
    steps(world, 3)  # the vine reaches (2, 0) and finds (3, 0) taken

    tip = world.tips[tip_id]
    assert tip_id in world._sleeping and tip.blocked
    assert world.sleeping_count == 1
    assert [world.step().visits for _ in range(5)] == [0, 0, 0, 0, 0]
    assert tip.cell == (2, 0) and tip.progress == 1


def test_a_tip_waiting_on_a_full_board_stays_awake():
    world = World(seed=1, max_cells=3)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    world.plant_seed((2, 0), VINE, "1/1000", "p2", direction=EAST)
    steps(world, 4)

    assert world.sleeping_count == 0
    assert [world.step().visits for _ in range(3)] == [1, 1, 1]


def test_nothing_sleeps_with_skipping_off():
    world, tip_id = blocked_vine()
    world.skip_stuck = False
    steps(world, 10)
    assert world.sleeping_count == 0 and world.tips[tip_id].blocked


def test_cutting_the_obstacle_wakes_the_tip_without_a_burst():
    world, tip_id = blocked_vine()
    steps(world, 10)
    assert tip_id in world._sleeping
    changes = world.cut((3, 0))  # the obstacle's root

    assert tip_id not in world._sleeping and tip_id in changes.woke
    world.step()
    assert world.tips[tip_id].cell == (3, 0)
    world.step()
    assert world.tips[tip_id].cell == (4, 0)


def walled_in(persistence: int):
    """A vine at (1, 0) heading east with its next hex and all four turns taken."""
    world = persistent_world(persistence)
    world.plant_seed((0, 0), "persistent", "1", "p1", direction=EAST)
    for hex in ((2, 0), (2, -1), (1, 1), (1, -1), (0, 1)):
        obstacle(world, hex)
    steps(world, 3)
    return world, own_tip(world)


def test_freeing_a_turn_hex_wakes_a_tip_that_had_nowhere_to_go():
    world, tip = walled_in(100)
    assert tip.id in world._sleeping and not tip.gave_up
    world.cut((1, -1))  # a root north-west of the tip

    assert tip.id not in world._sleeping
    world.step()
    assert tip.cell == (1, -1) and tip.heading == NORTH_WEST


def test_an_unrelated_cut_leaves_the_tip_asleep():
    world, tip = walled_in(100)
    obstacle(world, (9, 9))
    world.cut((9, 9))
    assert tip.id in world._sleeping


def test_a_tip_that_gave_up_is_not_woken_by_a_freed_turn():
    world, tip_id = blocked_vine()  # persistence 0: it gives up at once
    obstacle(world, (3, -1))  # north-east of (2, 0)
    steps(world, 3)
    assert world.tips[tip_id].gave_up and tip_id in world._sleeping

    world.cut((3, -1))
    assert tip_id in world._sleeping
    steps(world, 3)
    assert world.tips[tip_id].cell == (2, 0)


def test_a_sleeping_tip_on_a_cut_cell_is_gone():
    world, tip_id = blocked_vine()
    steps(world, 10)
    changes = world.cut((1, 0))  # the vine itself, behind its tip

    assert tip_id not in world.tips and tip_id not in world._sleeping
    assert tip_id in changes.woke
    assert all(tip_id not in ids for ids in world._watchers.values())


def test_switching_off_wakes_every_sleeping_tip():
    world, tip_id = blocked_vine()
    steps(world, 10)
    changes = world.set_skip_stuck(False)

    assert world.sleeping_count == 0 and changes.woke == [tip_id]
    assert world.step().visits == 1


def test_clear_forgets_sleeping_tips():
    world, _ = blocked_vine()
    steps(world, 10)
    world.clear()
    assert world.sleeping_count == 0 and not world._watchers


def equivalence_script(world: World, toggles: bool):
    """A crowded session with many cuts. Yields after every iteration.

    Choices depend only on the board, so two boards in the same state make
    the same ones. With ``toggles`` the world also switches skipping on and off.
    """
    world.scatter(60, (0, 0), 9, 7, "p1")
    world.scatter(40, (0, 0), 9, 7, "p1", persistence=100)
    for tick in range(200):
        if toggles and tick % 37 == 5:
            world.set_skip_stuck(not world.skip_stuck)
        segments = sorted(hex for hex, cell in world.cells.items() if cell.kind == SEGMENT)
        if segments and tick % 9 == 4:
            world.cut(segments[(tick * 7919) % len(segments)])
        if segments and tick % 23 == 11:
            start = segments[(tick * 104729) % len(segments)]
            world.slice([(start[0] + dq, start[1]) for dq in range(-4, 5)])
        if tick % 13 == 6:
            # Remove the plant in front of a stuck tip by cutting its root, so the
            # hex it waits on is emptied. (A cut anywhere else leaves a stump.)
            stuck = sorted(tip.id for tip in world.tips.values() if tip.blocked)
            if stuck:
                tip = world.tips[stuck[len(stuck) // 2]]
                ahead = world.cells.get(neighbor(tip.cell, tip.heading))
                if ahead is not None and ahead.plant_id != tip.plant_id:
                    world.cut(world.plants[ahead.plant_id].root)
        if tick == 100:
            world.clear()
            world.scatter(80, (0, 0), 10, 8, "p1", persistence=70)
        yield world.step().visits


def tips_state(world: World):
    return sorted((tip.to_dict() for tip in world.tips.values()), key=lambda tip: tip["id"])


def board_state(world: World):
    return board(world), tips_state(world), world.plants_snapshot(), world.rng.getstate()


@pytest.mark.parametrize("toggles", [False, True])
def test_skipping_stuck_tips_never_changes_the_game(toggles):
    skipping, plain = World(seed=21), World(seed=21)
    plain.skip_stuck = False
    slept = 0
    for tick, (skipping_visits, plain_visits) in enumerate(
        zip(equivalence_script(skipping, toggles), equivalence_script(plain, False))
    ):
        # Every iteration: every random draw, every tip, and the cell count;
        # the whole board every tenth iteration and at the end.
        assert skipping.rng.getstate() == plain.rng.getstate()
        assert tips_state(skipping) == tips_state(plain)
        assert len(skipping.cells) == len(plain.cells)
        if tick % 10 == 0:
            assert board_state(skipping) == board_state(plain)
        assert skipping_visits <= plain_visits
        slept = max(slept, skipping.sleeping_count)
    assert board_state(skipping) == board_state(plain)
    assert slept > 50  # the session really did put tips to sleep
    assert plain.sleeping_count == 0
