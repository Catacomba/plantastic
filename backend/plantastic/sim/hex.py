"""Axial hex coordinates for a pointy-top grid.

Directions are indexed 0 to 5 clockwise as seen on screen, starting at east.
The frontend's ``hex.js`` uses the same table.
"""

Hex = tuple[int, int]

DIRECTIONS: tuple[Hex, ...] = (
    (1, 0),    # 0 east
    (0, 1),    # 1 south-east
    (-1, 1),   # 2 south-west
    (-1, 0),   # 3 west
    (0, -1),   # 4 north-west
    (1, -1),   # 5 north-east
)

DIRECTION_NAMES = ("E", "SE", "SW", "W", "NW", "NE")


def neighbor(hex: Hex, direction: int) -> Hex:
    dq, dr = DIRECTIONS[direction % 6]
    return (hex[0] + dq, hex[1] + dr)


def neighbors(hex: Hex) -> list[Hex]:
    return [neighbor(hex, d) for d in range(6)]


def turn_left(direction: int) -> int:
    return (direction - 1) % 6


def turn_right(direction: int) -> int:
    return (direction + 1) % 6


def opposite(direction: int) -> int:
    return (direction + 3) % 6


def direction_between(origin: Hex, target: Hex) -> int:
    """The direction that leads from ``origin`` to the adjacent ``target``."""
    delta = (target[0] - origin[0], target[1] - origin[1])
    try:
        return DIRECTIONS.index(delta)
    except ValueError:
        raise ValueError(f"{origin} and {target} are not adjacent") from None
