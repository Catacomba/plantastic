import math

import pytest

from plantastic.sim.hex import (
    DIRECTIONS,
    direction_between,
    neighbor,
    neighbors,
    opposite,
    turn_left,
    turn_right,
)


def test_six_right_turns_return_to_start():
    for start in range(6):
        heading = start
        for _ in range(6):
            heading = turn_right(heading)
        assert heading == start


def test_left_undoes_right():
    for heading in range(6):
        assert turn_left(turn_right(heading)) == heading


def test_opposite_directions_cancel():
    for heading in range(6):
        assert neighbor(neighbor((3, -2), heading), opposite(heading)) == (3, -2)


def test_six_distinct_neighbors():
    assert len(set(neighbors((0, 0)))) == 6
    assert (0, 0) not in neighbors((0, 0))


def test_directions_are_clockwise_from_east():
    # Screen angle of a pointy-top hex direction, with y pointing down.
    def screen_angle(direction):
        q, r = DIRECTIONS[direction]
        return math.atan2(r, q + r / 2) % (2 * math.pi)

    angles = [screen_angle(d) for d in range(6)]
    assert angles == sorted(angles)
    assert DIRECTIONS[0] == (1, 0)


def test_direction_between():
    for heading in range(6):
        assert direction_between((1, 1), neighbor((1, 1), heading)) == heading
    with pytest.raises(ValueError):
        direction_between((0, 0), (2, 0))
