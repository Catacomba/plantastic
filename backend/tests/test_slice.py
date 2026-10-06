from plantastic.sim.world import ROOT, SEGMENT, STUMP, World

from .helpers import EAST, NORTH_EAST, SOUTH_EAST, VINE, board, east_vine, steps, tips_at


def two_vines() -> World:
    """Two east vines of 6, rooted at (0, 0) and (0, 4)."""
    world = World(seed=1)
    world.plant_seed((0, 0), VINE, "1", "p1", direction=EAST)
    world.plant_seed((0, 4), VINE, "1", "p2", direction=EAST)
    steps(world, 6)
    return world


def stumps(world: World) -> set:
    return {hex for hex, cell in world.cells.items() if cell.kind == STUMP}


def test_path_across_two_vines_cuts_both():
    world = two_vines()
    world.slice([(3, 0), (3, 1), (3, 2), (3, 3), (3, 4)])

    assert stumps(world) == {(3, 0), (3, 4)}
    for row in (0, 4):
        assert all((q, row) not in world.cells for q in (4, 5, 6))
        assert tips_at(world, (1, row)) == [SOUTH_EAST, NORTH_EAST]
    assert all((3, r) not in world.cells for r in (1, 2, 3))


def test_path_with_nothing_to_cut_changes_nothing():
    world = east_vine(6)
    world.cut((4, 0))
    before = (board(world), world.tips_snapshot())

    changes = world.slice([(9, 9), (4, 0), (9, 8), (-3, 2)])

    assert (board(world), world.tips_snapshot()) == before
    assert changes.added == changes.changed == changes.removed == []


def test_slice_does_not_advance_the_iteration():
    world = two_vines()
    world.slice([(3, 0), (3, 4), (2, 0), (2, 4)])
    assert world.tick == 6


def test_path_from_root_toward_tip_leaves_the_first_cut():
    world = east_vine(6)
    world.slice([(2, 0), (3, 0), (4, 0), (5, 0)])

    assert set(world.cells) == {(0, 0), (1, 0), (2, 0)}
    assert stumps(world) == {(2, 0)}


def test_path_from_tip_toward_root_leaves_only_the_last_cut():
    world = east_vine(6)
    world.slice([(5, 0), (4, 0), (3, 0)])

    assert set(world.cells) == {(0, 0), (1, 0), (2, 0), (3, 0)}
    assert stumps(world) == {(3, 0)}
    # Every cut gets its cut response. The forks from the first cut sat on
    # (3, 0) and went with it; those from the second and third remain.
    assert tips_at(world, (2, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert tips_at(world, (1, 0)) == [SOUTH_EAST, NORTH_EAST]
    assert len(world.tips) == 4


def test_path_over_a_root_leaves_the_plant():
    world = two_vines()
    world.slice([(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 4)])

    assert world.cells[(0, 0)].kind == ROOT
    assert world.cells[(0, 4)].kind == ROOT
    assert world.cells[(3, 0)].kind == SEGMENT
    assert stumps(world) == {(1, 4)}
    assert len(world.plants) == 2


def test_one_hex_path_on_a_root_changes_nothing():
    world = east_vine(4)
    before = (board(world), world.tips_snapshot())
    world.slice([(0, 0)])
    assert (board(world), world.tips_snapshot()) == before


def test_slice_changes_replay_onto_a_client_board():
    world = two_vines()
    client = board(world)

    world.slice([(5, 0), (4, 0), (3, 0), (3, 1), (3, 4)]).apply_to(client)
    assert client == board(world)

    steps(world, 3)
    client = board(world)
    world.slice([(2, -1), (2, 0), (2, 1), (1, 0), (2, 4)]).apply_to(client)
    assert client == board(world)
