"""The engine rules every species relies on: turning, branching, ending, and deciding once per hex."""

from plantastic.sim.species import Shoot, Species
from plantastic.sim.world import World

from .helpers import EAST, NORTH_EAST, SOUTH_EAST, VINE, steps, tips_at


class Scripted(Species):
    """Plays back a list of decisions, one for each call to ``grow``, then goes straight."""

    id = "scripted"
    name = "Scripted"

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def grow(self, tip, plant, world):
        self.calls += 1
        if self.script:
            return self.script.pop(0)(tip)
        return [Shoot(tip.heading)]


class Gambler(Species):
    """Draws a random number and branches both ways on every decision."""

    id = "gambler"
    name = "Gambler"

    def __init__(self):
        self.calls = 0

    def grow(self, tip, plant, world):
        self.calls += 1
        world.rng.random()
        return [Shoot(tip.heading), Shoot(tip.heading - 1), Shoot(tip.heading + 1)]


def scripted_world(script, **kwargs):
    species = Scripted(script)
    world = World(seed=1, catalog={species.id: species, **kwargs.pop("extra", {})}, **kwargs)
    world.plant_seed((0, 0), species.id, "1", "p1", direction=EAST)
    return world, species


def test_turn_joins_the_new_cell_to_the_one_it_left():
    world, _ = scripted_world([lambda tip: [Shoot(SOUTH_EAST)]])
    world.step()

    assert world.cells[(0, 1)].parent == (0, 0)
    (tip,) = world.tips.values()
    assert tip.cell == (0, 1) and tip.heading == SOUTH_EAST


def test_branch_leaves_a_tip_on_the_cell_it_left():
    world, _ = scripted_world([lambda tip: [Shoot(EAST), Shoot(NORTH_EAST)]])
    world.step()

    assert tips_at(world, (1, 0)) == [EAST]
    assert tips_at(world, (0, 0)) == [NORTH_EAST]
    side = next(tip for tip in world.tips.values() if tip.cell == (0, 0))
    assert side.progress == 0
    assert (1, -1) not in world.cells

    world.step()
    assert world.cells[(1, -1)].parent == (0, 0)


def test_branch_without_room_is_not_created():
    from plantastic.sim.species import CATALOG

    world, _ = scripted_world([lambda tip: [Shoot(EAST), Shoot(NORTH_EAST)]], extra={VINE: CATALOG[VINE]})
    world.plant_seed((1, -1), VINE, "1/1000", "p2", direction=NORTH_EAST)
    world.step()

    assert tips_at(world, (1, 0)) == [EAST]
    assert tips_at(world, (0, 0)) == []


def test_empty_decision_ends_the_tip_and_keeps_its_cells():
    world, _ = scripted_world([lambda tip: [Shoot(EAST)], lambda tip: [Shoot(EAST), Shoot(NORTH_EAST)], lambda tip: []])
    steps(world, 5)

    assert (1, 0) in world.cells and (2, 0) in world.cells
    assert (3, 0) not in world.cells
    # The stem's tip is gone; the side branch keeps growing.
    assert [tip.heading for tip in world.tips.values()] == [NORTH_EAST]
    assert (4, -3) in world.cells


def test_last_removes_the_tip_as_it_enters_its_final_hex():
    world, _ = scripted_world([lambda tip: [Shoot(EAST)], lambda tip: [Shoot(EAST, last=True)]])
    world.step()
    assert len(world.tips) == 1
    world.step()

    assert (2, 0) in world.cells
    assert not world.tips
    steps(world, 3)
    assert (3, 0) not in world.cells


def test_shoot_state_replaces_the_tips_state():
    world, _ = scripted_world([lambda tip: [Shoot(EAST, {"note": 7})], lambda tip: [Shoot(EAST)]])
    world.step()
    (tip,) = world.tips.values()
    assert tip.state == {"note": 7}
    world.step()
    assert tip.state == {"note": 7}


def test_tip_blocked_by_a_cell_decides_once():
    from plantastic.sim.species import CATALOG

    gambler = Gambler()
    world = World(seed=1, catalog={gambler.id: gambler, VINE: CATALOG[VINE]})
    world.plant_seed((0, 0), gambler.id, "1", "p1", direction=EAST)
    world.plant_seed((1, 0), VINE, "1/1000", "p2", direction=EAST)
    world.plant_seed((1, -1), VINE, "1/1000", "p2", direction=EAST)
    world.plant_seed((0, 1), VINE, "1/1000", "p2", direction=EAST)

    steps(world, 20)
    assert gambler.calls == 1
    assert len([tip for tip in world.tips.values() if tip.plant_id == 1]) == 1
    rng_state = world.rng.getstate()
    steps(world, 5)
    assert world.rng.getstate() == rng_state

    world.cut((1, 0))  # the obstacle is a root, so this removes it
    world.step()
    assert world.cells[(1, 0)].plant_id == 1
    assert gambler.calls == 1
    world.step()
    assert gambler.calls == 2


def test_tip_stopped_by_a_full_board_decides_once():
    gambler = Gambler()
    world = World(seed=1, catalog={gambler.id: gambler}, max_cells=1)
    world.plant_seed((0, 0), gambler.id, "1", "p1", direction=EAST)

    assert world.step().full
    # The branches sprouted by the first decision each decide once in turn,
    # until all six directions around the root hold a waiting tip.
    steps(world, 5)
    assert len(world.tips) == 6
    assert gambler.calls == 6
    rng_state = world.rng.getstate()

    steps(world, 20)
    assert gambler.calls == 6
    assert len(world.tips) == 6
    assert world.rng.getstate() == rng_state
    assert len(world.cells) == 1

    world.max_cells = 2
    world.step()
    assert (1, 0) in world.cells  # the first tip advanced the way it decided before the wait
    assert gambler.calls == 6


# -- persistence ----------------------------------------------------------------


def stubborn_world(persistence: int, seed: int = 1, script=()):
    """A scripted plant heading east from (0, 0), with (2, 0) already taken."""
    from plantastic.sim.species import CATALOG

    species = Scripted(script)
    species.persistence = persistence
    world = World(seed=seed, catalog={species.id: species, VINE: CATALOG[VINE]})
    world.plant_seed((0, 0), species.id, "1", "p1", direction=EAST)
    world.plant_seed((2, 0), VINE, "1/1000", "p2", direction=EAST)
    return world, species


def own(world):
    return next(tip for tip in world.tips.values() if tip.plant_id == 1)


def test_tip_that_gives_up_waits_without_rolling_again():
    world, _ = stubborn_world(1)  # the roll fails for this seed
    world.step()
    before = world.rng.getstate()
    world.step()
    assert world.rng.getstate() != before  # one roll for this hex
    tip = own(world)
    assert tip.blocked and tip.cell == (1, 0) and tip.heading == EAST
    rng_state = world.rng.getstate()

    steps(world, 20)
    assert tip.blocked and tip.cell == (1, 0) and tip.heading == EAST
    assert world.rng.getstate() == rng_state


def test_tip_that_gave_up_resumes_its_way_and_rolls_again_at_the_next_obstacle():
    world, _ = stubborn_world(1)
    world.plant_seed((4, 0), VINE, "1/1000", "p2", direction=EAST)
    steps(world, 5)
    world.cut((2, 0))  # a root, so the whole obstacle goes

    world.step()
    tip = own(world)
    assert tip.cell == (2, 0) and tip.heading == EAST
    world.step()
    assert tip.cell == (3, 0)
    rng_state = world.rng.getstate()
    world.step()  # (4, 0) is taken: a fresh roll
    assert world.rng.getstate() != rng_state


def test_detoured_tip_rolls_again_at_its_next_obstacle():
    world, _ = stubborn_world(100)
    world.plant_seed((2, -1), VINE, "1/1000", "p2", direction=EAST)  # leaves only south-east
    world.plant_seed((1, 3), VINE, "1/1000", "p2", direction=EAST)  # in the way after the detour
    steps(world, 3)
    tip = own(world)
    assert tip.cell == (1, 2) and tip.heading == SOUTH_EAST

    world.step()
    assert not tip.blocked
    assert tip.cell in {(2, 2), (0, 3)}


def test_persistence_is_honoured_roughly():
    taken = 0
    for seed in range(400):
        world, _ = stubborn_world(30, seed=seed)
        steps(world, 2)
        taken += not own(world).blocked
    assert 0.2 <= taken / 400 <= 0.4


def test_last_hex_is_entered_by_another_path_and_then_the_tip_ends():
    world, species = stubborn_world(100, script=[lambda tip: [Shoot(EAST)], lambda tip: [Shoot(EAST, last=True)]])
    world.plant_seed((2, -1), VINE, "1/1000", "p2", direction=EAST)
    steps(world, 2)

    assert world.cells[(1, 1)].plant_id == 1
    assert all(tip.plant_id != 1 for tip in world.tips.values())
    steps(world, 3)
    assert species.calls == 2
