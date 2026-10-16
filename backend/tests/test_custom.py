"""The custom plant: growth, branching, and settings that stay with the plant."""

from collections import Counter

from plantastic.sim.hex import direction_between
from plantastic.sim.world import ROOT, World

from .helpers import EAST, VINE, board, steps

DEFAULTS = {
    "branch_chance": 0,
    "branch_min": 1,
    "branch_max": 1,
    "calm_min": 0,
    "calm_max": None,
    "turn_chance": 0,
    "persistence": 0,
    "cut_response": "fork",
}


def custom(seed: int = 1, hex=(0, 0), world: World | None = None, **settings) -> World:
    world = world or World(seed=seed)
    world.plant_seed(hex, "custom", "1", "p1", direction=EAST, settings={**DEFAULTS, **settings})
    return world


def children(world: World, hex) -> list:
    return [cell.hex for cell in world.cells.values() if cell.parent == hex]


def main_path(world: World, plant_id: int = 1) -> list:
    """Follow a plant from its root, always taking the oldest child."""
    path = [next(cell.hex for cell in world.cells.values() if cell.plant_id == plant_id and cell.kind == ROOT)]
    while children(world, path[-1]):
        path.append(children(world, path[-1])[0])
    return path


def straight_runs(path: list) -> list:
    """Lengths of the straight stretches along a path."""
    taken = [direction_between(a, b) for a, b in zip(path, path[1:])]
    runs, length = [], 1
    for previous, current in zip(taken, taken[1:]):
        if current == previous:
            length += 1
        else:
            runs.append(length)
            length = 1
    return runs + [length]


def test_no_chances_and_no_limit_grows_straight_forever():
    world = custom()
    steps(world, 60)
    assert set(world.cells) == {(n, 0) for n in range(61)}
    assert len(world.tips) == 1


def test_calm_maximum_forces_a_turn_every_three_hexes():
    world = custom(calm_min=0, calm_max=3)
    steps(world, 16)  # stop before the path can come back round to itself
    runs = straight_runs(main_path(world))

    # Three hexes straight, then the forced turn's hex begins the next stretch.
    assert runs[0] == 3
    assert all(run == 4 for run in runs[1:-1])
    assert len(world.tips) == 1


def test_calm_minimum_delays_every_event():
    for seed in range(5):
        world = custom(seed=seed, calm_min=5, turn_chance=100)
        steps(world, 17)
        runs = straight_runs(main_path(world))

        # Five calm hexes, then a turn whose hex starts the next stretch.
        assert runs[0] == 5
        assert all(run == 6 for run in runs[1:-1])


def test_calm_minimum_applies_to_branches_too():
    world = custom(calm_min=5, branch_chance=100)
    steps(world, 5)
    assert len(world.tips) == 1
    world.step()
    assert len(world.tips) == 2
    branch_point = (5, 0)
    assert [tip.cell for tip in world.tips.values()].count(branch_point) == 1


def test_branch_chance_of_one_hundred_branches_on_every_step():
    world = custom(branch_chance=100)
    world.step()
    assert len(world.tips) == 2
    stem = [(1, 0), (2, 0), (3, 0)]
    steps(world, 2)
    assert all(hex in world.cells for hex in stem)
    # Every cell the main tip left has at least one side branch. Side tips
    # branch as they leave too, so a cell can gain more than one.
    for hex in [(0, 0), (1, 0)]:
        assert len(children(world, hex)) >= 2


def test_fixed_branch_count_sprouts_that_many_in_different_directions():
    world = custom(branch_chance=100, branch_min=2, branch_max=2)
    world.step()

    side_tips = [tip for tip in world.tips.values() if tip.cell == (0, 0)]
    assert len(side_tips) == 2
    assert len({tip.heading for tip in side_tips}) == 2
    assert all(tip.heading in (1, 2, 4, 5) for tip in side_tips)  # never straight on or straight back
    assert [tip.cell for tip in world.tips.values()].count((1, 0)) == 1
    assert all(tip.state == {"calm": 0} for tip in world.tips.values())


def test_branch_count_range_produces_each_count():
    seen = Counter()
    for seed in range(60):
        world = custom(seed=seed, branch_chance=100, branch_min=1, branch_max=3)
        world.step()
        seen[len(world.tips) - 1] += 1
    assert set(seen) == {1, 2, 3}


def test_branching_uses_only_the_room_there_is():
    world = World(seed=1)
    for hex in [(1, -1), (-1, 1), (0, -1)]:  # three of the four side hexes of the root
        world.plant_seed(hex, VINE, "1/1000", "p2", direction=EAST)
    custom(world=world, branch_chance=100, branch_min=4, branch_max=4)
    world.step()

    side_tips = [tip for tip in world.tips.values() if tip.cell == (0, 0)]
    assert [tip.heading for tip in side_tips] == [1]  # south-east is the only side with room


def test_turns_go_both_ways_about_equally():
    turns = Counter()
    for seed in range(200):
        world = custom(seed=seed, turn_chance=100)
        world.step()
        turns[next(iter(world.tips.values())).heading] += 1
    assert set(turns) == {1, 5}
    assert 70 <= turns[1] <= 130


def test_forced_event_follows_the_proportion_of_the_chances():
    outcomes = Counter()
    for seed in range(300):
        world = custom(seed=seed, calm_max=0, branch_chance=30, turn_chance=10)
        world.step()
        outcomes["branch" if len(world.tips) == 2 else "turn"] += 1
    # Forced on every step, three branches for every turn.
    assert outcomes["branch"] + outcomes["turn"] == 300
    assert 190 <= outcomes["branch"] <= 260


def test_branch_chance_is_roughly_honoured():
    branched = 0
    for seed in range(400):
        world = custom(seed=seed, branch_chance=25)
        world.step()
        branched += len(world.tips) == 2
    assert 70 <= branched <= 130


def test_each_plant_keeps_the_settings_it_was_planted_with():
    world = World(seed=1)
    custom(world=world, hex=(0, 0))
    first_settings = dict(world.plants[1].settings)
    custom(world=world, hex=(0, 30), turn_chance=100, calm_max=0)
    steps(world, 12)

    assert world.plants[1].settings == first_settings
    assert world.plants[2].settings["turn_chance"] == 100
    # The first still grows dead straight; the second turns on every step.
    assert main_path(world, 1) == [(n, 0) for n in range(13)]
    second = main_path(world, 2)
    assert straight_runs(second)[:3] == [1, 1, 1]


def run_with_a_blocked_period(seed: int) -> list:
    world = World(seed=seed)
    history = []
    custom(world=world, hex=(0, 0), branch_chance=30, branch_max=2, turn_chance=20, calm_min=1, calm_max=6)
    custom(world=world, hex=(6, 0), branch_chance=20, turn_chance=30, cut_response="regrow")
    world.plant_seed((3, 0), VINE, "1/1000", "p2", direction=EAST)  # stands in the first plant's way
    for tick in range(50):
        if tick == 20:
            world.cut((3, 0))
        if tick == 30:
            segments = sorted(cell.hex for cell in world.cells.values() if cell.kind == "segment")
            world.cut(segments[len(segments) // 2])
        world.step()
        history.append((board(world), world.tips_snapshot()))
    return history


def test_custom_plants_replay_identically_through_a_blocked_period():
    assert run_with_a_blocked_period(8) == run_with_a_blocked_period(8)
    assert run_with_a_blocked_period(8) != run_with_a_blocked_period(9)
