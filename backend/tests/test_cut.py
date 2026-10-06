import pytest

from plantastic.sim.world import ROOT, SEGMENT, STUMP, Changes, SimError, World

from .helpers import EAST, NORTH_EAST, NORTH_WEST, SOUTH_EAST, VINE, board, east_vine, steps, tips_at


def forked_vine() -> World:
    """An east vine of 6 cut at cell 5, with both forks grown 3 cells."""
    world = east_vine(6)
    world.cut((5, 0))
    steps(world, 3)
    return world


# -- generic cut -----------------------------------------------------------


def test_cut_in_the_middle_leaves_a_stump_and_removes_the_rest():
    world = east_vine(6)
    world.cut((4, 0))

    assert world.cells[(4, 0)].kind == STUMP
    assert (5, 0) not in world.cells and (6, 0) not in world.cells
    assert [world.cells[(n, 0)].kind for n in range(4)] == [ROOT, SEGMENT, SEGMENT, SEGMENT]
    assert not tips_at(world, (6, 0))


def test_cutting_the_tip_cell_removes_its_tip():
    world = east_vine(3)
    world.cut((3, 0))

    assert world.cells[(3, 0)].kind == STUMP
    assert not tips_at(world, (3, 0))


def test_stump_never_grows():
    world = east_vine(3)
    world.cut((3, 0))
    steps(world, 5)
    assert (4, 0) not in world.cells


def test_severed_branches_and_stumps_are_removed():
    world = forked_vine()
    assert world.cells[(5, 0)].kind == STUMP
    assert (6, -3) in world.cells and (3, 3) in world.cells

    world.cut((1, 0))

    assert set(world.cells) == {(0, 0), (1, 0)}
    assert world.cells[(1, 0)].kind == STUMP
    assert all(tip.cell == (0, 0) for tip in world.tips.values())


def test_cutting_the_root_removes_the_whole_plant():
    world = forked_vine()
    world.plant_seed((0, 9), VINE, "1", "p2", direction=EAST)

    world.cut((0, 0))

    assert set(world.cells) == {(0, 9)}
    assert list(world.plants) == [2]
    assert all(tip.plant_id == 2 for tip in world.tips.values())


@pytest.mark.parametrize("target", [(4, 0), (9, 9)], ids=["stump", "empty"])
def test_cutting_a_stump_or_empty_hex_is_rejected(target):
    world = east_vine(6)
    world.cut((4, 0))
    before = (board(world), world.tips_snapshot())

    with pytest.raises(SimError) as error:
        world.cut(target)

    assert error.value.code == "nothing_to_cut"
    assert (board(world), world.tips_snapshot()) == before


# -- straight vine cut response --------------------------------------------


def test_fork_sprouts_two_cells_behind_the_stump():
    world = east_vine(6)
    world.cut((5, 0))

    assert world.cells[(5, 0)].kind == STUMP
    assert (6, 0) not in world.cells
    assert tips_at(world, (3, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 2
    assert all(tip.progress == 0 for tip in world.tips.values())


def test_forks_keep_their_direction():
    world = forked_vine()
    for n in range(1, 4):
        assert world.cells[(3 + n, -n)].kind == SEGMENT  # north-east
        assert world.cells[(3, n)].kind == SEGMENT  # south-east
    assert tips_at(world, (6, -3)) == [NORTH_EAST]
    assert tips_at(world, (3, 3)) == [SOUTH_EAST]


def test_fork_appears_after_one_growth_interval():
    world = east_vine(6, speed="0.5")
    world.cut((5, 0))

    world.step()
    assert (4, -1) not in world.cells and (3, 1) not in world.cells
    world.step()
    assert (4, -1) in world.cells and (3, 1) in world.cells


@pytest.mark.parametrize("cut_at", [(1, 0), (2, 0)])
def test_cut_near_the_root_sprouts_from_the_root(cut_at):
    world = east_vine(4)
    world.cut(cut_at)

    assert world.cells[cut_at].kind == STUMP
    assert tips_at(world, (0, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 2


def test_forward_follows_the_bend_and_an_occupied_side_is_skipped():
    # The north-east fork leaves (3, 0) at a bend. Cutting it two cells out
    # sprouts from (3, 0) again, with north-east as forward: north-west has
    # room, east is the old vine.
    world = forked_vine()
    world.cut((5, -2))

    assert world.cells[(5, -2)].kind == STUMP
    assert (6, -3) not in world.cells
    assert tips_at(world, (3, 0)) == [NORTH_WEST]
    assert (4, 0) in world.cells


def test_no_sprouts_when_both_sides_are_occupied():
    world = east_vine(6)
    world.plant_seed((4, -1), VINE, "1/1000", "p2", direction=NORTH_EAST)
    world.plant_seed((3, 1), VINE, "1/1000", "p2", direction=SOUTH_EAST)

    world.cut((5, 0))

    assert world.cells[(5, 0)].kind == STUMP
    assert (6, 0) not in world.cells
    assert not [tip for tip in world.tips.values() if tip.plant_id == 1]


def test_no_duplicate_tip_on_the_same_cell_and_heading():
    world = east_vine(6)
    world.cut((5, 0))
    plant = world.plants[1]

    assert not world.can_sprout(plant, (3, 0), NORTH_EAST)
    assert world.can_sprout(plant, (2, 0), NORTH_EAST)


# -- change records --------------------------------------------------------


def test_replaying_change_records_reproduces_the_world():
    world = World(seed=5)
    client: dict = {}

    def apply(changes: Changes) -> None:
        changes.apply_to(client)
        assert client == board(world)

    apply(world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST))
    apply(world.plant_seed((0, 6), VINE, "2", "p1", direction=EAST))
    for _ in range(6):
        apply(world.step())
    apply(world.cut((5, 0)))
    for _ in range(4):
        apply(world.step())
    apply(world.cut((5, -2)))
    apply(world.cut((0, 6)))
    apply(world.plant_seed((2, 6), VINE, "1", "p1", direction=EAST))
    for _ in range(3):
        apply(world.step())
    apply(world.cut((1, 0)))


def test_merged_change_records_replay_the_same_as_separate_ones():
    world = World(seed=5)
    merged = Changes()
    merged.merge(world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST))
    for _ in range(6):
        merged.merge(world.step())
    merged.merge(world.cut((3, 0)))  # removes cells added earlier in the record
    for _ in range(3):
        merged.merge(world.step())
    merged.merge(world.cut((0, 0)))  # removes everything
    merged.merge(world.plant_seed((1, 0), VINE, "1", "p1", direction=EAST))
    merged.merge(world.step())

    client: dict = {}
    merged.apply_to(client)
    assert client == board(world)
