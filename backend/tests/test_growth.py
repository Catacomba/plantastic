import pytest

from plantastic.sim.world import SimError, World

from .helpers import EAST, VINE, WEST, board, east_vine, steps


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
